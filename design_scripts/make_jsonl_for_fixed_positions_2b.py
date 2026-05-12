import os, sys, shutil, glob, json

#Modify these variables as needed
jsonl_dir = '../../jsonl_dir'
pdb_dir = '../../pdb_dir'
chains_to_design="A"
fixed_positions_jsonl_dir = f'{jsonl_dir}/fixed_positions_jsonl'

def find_matcher_pos(pdb_file):
    pos = []
    designable = []
    with open(pdb_file,'r') as pdb:
        for line in pdb:
            if line.startswith('REMARK 666 MATCH'):
                pos.append(line.strip().split()[11])
            if 'designable' in line:
                designable.append(line.strip().split()[2])
            
    return set(pos+designable)


pdb_list = glob.glob(f'{pdb_dir}/*.pdb')

for pdb in pdb_list:
    pdb_name = os.path.basename(pdb).replace('.pdb','')
    
    fixed_positions=[int(item) for item in find_matcher_pos(pdb)]
    
    fixed_positions_dict = dict({pdb_name : {chains_to_design: fixed_positions} })

    path_for_fixed_positions= f'{fixed_positions_jsonl_dir}/{pdb_name}.jsonl'

    with open(path_for_fixed_positions, 'w') as f:
        f.write(json.dumps(fixed_positions_dict) + '\n')