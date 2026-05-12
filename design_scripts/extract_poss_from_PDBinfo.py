import os, sys, shutil, glob

def extract_poss_from_PDBinfo(pdb_path,
                              write_posfile=False,
                              posfile_path=None,
                              repeat_for_n_csts = 1):
    pocket_poss = []
    hbres_poss = []
    with open(pdb_path,'r') as pdb:
        for line in pdb:
#REMARK PDBinfo-LABEL:   40 pocket hbnet_idx_6 hbnet_resn_R
#REMARK PDBinfo-LABEL:   42 pocket
#REMARK PDBinfo-LABEL:   48 pocket
#REMARK PDBinfo-LABEL:   49 pocket hbnet_idx_7 hbnet_resn_R
#REMARK PDBinfo-LABEL:   50 pocket hbnet_idx_7 hbnet_resn_E
            if line.startswith('REMARK PDBinfo-LABEL:') and "pocket" in line and not "hbnet_" in line: #core positions, not in core polar network
                tokens = line.strip().split()
                resi = int(tokens[2])
                pocket_poss.append(resi)

            elif line.startswith('REMARK PDBinfo-LABEL:') and "hbnet_" in line: #core and boundary(?) positions forming core polar network
                tokens = line.strip().split()
                #hbresn = tokens[3].split("_")[1]
                hbresi = int(tokens[2])
                hbres_poss.append(hbresi)
            else:
                continue

    return pocket_poss, hbres_poss