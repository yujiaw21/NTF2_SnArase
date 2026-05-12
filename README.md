# Computational Enzyme Design Pipeline

This repository contains the computational enzyme design pipeline as described in **De novo proteins featuring an activated arginine are potent SNAr biocatalysts**.


---

## Overview

The pipeline proceeds through four main stages:

```
RosettaMatch
    └── Theozyme placement into scaffold library
Sequence Design (three parallel strategies)
    ├── Rosetta Interface Design
    ├── Rosetta–LigandMPNN Hybrid
    └── LigandMPNN-Based Design
Filtering
    └── Shape complementarity, active site geometry, AF2 quality metrics
AlphaFold2 Validation
    └── pLDDT, pTM, RMSD to design model
```

---

## Repository Structure

```
.
├── design_scripts/            # Design scripts and intermediate files for all three strategies
├── dft_coordinates/          # DFT coordinates of theozymes (.xyz)
├── ligand_params/            # Ligand parameter files (.params)
├── constraints/              # Geometric constraint files (.cst)
├── ntf2_scaffolds/           # NTF2 scaffolds for RosettaMatch
├── protein_designs/          # Final designs passing all filters and entering yeast surface display (.pdb)
└── README.md
```

---

## Dependencies

| Tool | Version | Notes |
|------|---------|-------|
| LigandMPNN |  | https://github.com/dauparas/LigandMPNN/ |
| AlphaFold2 | 2.2.2 | https://github.com/google-deepmind/alphafold/ |
| Python |3.10.13 | |
| PyRosetta | 2024.15 | https://www.pyrosetta.org/ |

---

## Stage 1: Theozyme Matching with RosettaMatch

Theozyme geometries derived from DFT transition state calculations were placed into a scaffold library using RosettaMatch.

```bash
$ROSETTAPATH/main/source/bin/match.hdf5.linuxgccrelease @{flags} -beta_nov16 -preserve_header true -s {pdb_file} -match:geometric_constraint_file {cst} -match::scaffold_active_site_residues_for_geomcsts geom_cst_pos.txt -extra_res_fa {params} -match:lig_name BHA -nstruct 1 >log_{pdb}.txt
```

**Key input files:**
- `flags` — flags file for additional Rosetta options. An example is provided at `design_scripts/matcher.flags.txt`
- `pdb_file` — scaffold PDB file. All input NTF2 scaffolds are provided at `ntf2_scaffolds/`
- `cst` — geometric constraint file defining theozyme geometry. Constraint files for each stereochemical configuration are provided at `constraints/`
- `geom_cst_pos.txt` — Use the script `design_scripts/extract_poss_from_PDBinfo.py` to generate the required `geom_cst_pos.txt` for RosettaMatch for each input scaffold
- `params` — ligand parameter file. All `.params` are provided at `ligand_params/`


The RosettaMatch output was filtered before sequence design using the following command.

```bash
$ROSETTAPATH/main/source/bin/rosetta_scripts.hdf5.linuxgccrelease -beta_nov16 -preserve_header true -s {pdb_path}  -parser:protocol {xml} -extra_res_fa {params} -parser:script_vars geom_cst="{cst}" -nstruct 1 -out:file:score_only {scorefile} >/dev/null
```

**Key input files:**
- `pdb_path` — RosettaMatch output.
- `xml` — Rosetta Script to score the input PDB file.  An example is provided at `design_scripts/score_pose.xml`
- `params` — ligand parameter file. All `.params` are provided at `ligand_params/`
- `cst` — geometric constraint file defining theozyme geometry. Constraint files for each stereochemical configuration are provided at `constraints/`


---

## Stage 2: Sequence Design

Three design strategies were applied in parallel to the RosettaMatch outputs.

### 2a. Rosetta Interface Design

```bash
$ROSETTAPATH/main/source/bin/rosetta_scripts.hdf5.linuxgccrelease -beta_nov16 -preserve_header true -s {pdb_path} -parser:protocol {xml} -extra_res_fa {params} -parser:script_vars geom_cst_pos_1="{pos[0]}" geom_cst_pos_2="{pos[1]}" geom_cst_pos_3="{pos[2]}" geom_cst="{cst}" -nstruct 1 -out:file:score_only {scorefile} >/dev/null
```

**Key input files:**
- `pdb_path` — RosettaMatch output.
- `xml` — RosettaScripts XML protocol for interface design. An example is provided at `design_scripts/enzdes.xml`
- `params`— ligand parameter file. All `.params` are provided at `ligand_params/`
- `pos[0], pos[1], pos[2]` — residue number of the catalytic histidine, aspartate/glutamate, arginine
- `cst` — geometric constraint file defining theozyme geometry. Constraint files for each stereochemical configuration are provided at `constraints/`

### 2b. Rosetta–LigandMPNN Hybrid

Rosetta was first used to optimise the protein–ligand interface, followed by LigandMPNN for sequence design.

```bash
# Step 1: Rosetta interface optimisation

See the example above in 2a.

# Step 2: LigandMPNN sequence design
python {mpnn_dir}/protein_mpnn_run.py \
    --pdb_path {pdb_path} \
    --pdb_path_chains A \
    --fixed_positions_jsonl {path_for_fixed_positions} \
    --ligand_params_path {params} \
    --out_folder {output_dir} \
    --num_seq_per_target 4 \
    --sampling_temp "0.1" \
    --batch_size 1
```

**Key input files:**
- `pdb_path` — Output `.pdb` file from step 1.
- `path_for_fixed_positions` — LigandMPNN jsonl file for defining which residues are fixed. Use the script `design_scripts/make_jsonl_for_fixed_positions_2b.py` to generate the required files.
- `params`— ligand parameter file. All `.params` are provided at `ligand_params/`



### 2c. LigandMPNN-Based Design

```bash
python {mpnn_dir}/protein_mpnn_run.py \
    --pdb_path {pdb_path} \
    --pdb_path_chains A \
    --fixed_positions_jsonl {path_for_fixed_positions} \
    --ligand_params_path {params} \
    --out_folder {output_dir} \
    --num_seq_per_target 4 \
    --sampling_temp "0.1" \
    --batch_size 1
```


**Key input files:**
- `pdb_path` — Output `.pdb` file from RosettaMatch.
- `path_for_fixed_positions` — LigandMPNN jsonl file for defining which residues are fixed. Use the script `design_scripts/make_jsonl_for_fixed_positions_2c.py` to generate the required files.
- `params`— ligand parameter file. All `.params` are provided at `ligand_params/`


---

## Stage 3: Filtering

Designs were filtered based on shape complementarity, active site geometry, and Rosetta energy terms. The following metrics and cutoffs were applied. For designs using LigandMPNN, the designed sequence was threaded back to the input Rosetta model using the following command.

```bash
$ROSETTAPATH/main/source/bin/rosetta_scripts.hdf5.linuxgccrelease -beta_nov16 -preserve_header true -s {pdb_path}  -parser:protocol {xml} -extra_res_fa {params} -parser:script_vars geom_cst_pos_1="{pos[0]}" geom_cst_pos_2="{pos[1]}"  geom_cst_pos_3="{pos[2]}" geom_cst="{cst}" mpnn_seq="{mpnn_seq}" -nstruct 1 >/dev/null
```

**Key input files:**
- `pdb_path` — Rosetta model from step 1, if using Rosetta-LigandMPNN hybrid design (2b); or RosettaMatch output if using full LigandMPNN design (2c)
- `xml` — RosettaScripts XML protocol for threading LigandMPNN sequence and relaxing. An example is provided at `design_scripts/thread_and_relax.xml`
- `params`— ligand parameter file. All `.params` are provided at `ligand_params/`
- `pos[0], pos[1], pos[2]` — residue number of the catalytic histidine, aspartate/glutamate, arginine
- `cst` — geometric constraint file defining theozyme geometry. Constraint files for each stereochemical configuration are provided at `constraints/`
- `mpnn_seq` — The protein sequence designed by LigandMPNN

---

## Stage 4: AlphaFold2 Validation

Designs passing filters were assessed using [AlphaFold2](https://github.com/google-deepmind/alphafold) to evaluate predicted structural quality and correspondence to the design model. Please refer to the official documentation for how to run AlphaFold2.


---

## Contact

For questions, please contact Yujia Wang at yujiaw21@uw.edu.