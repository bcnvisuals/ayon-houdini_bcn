import hou
import json

def add_custom_aov():

    out = hou.node("/out")

    # check if a Redshift_AOVs already exists
    existing = [n for n in out.children() if n.type().name() == "Redshift_AOVs"]

    if existing:
        aovs = existing[0]
        print("Already exists:", aovs.path())
    else:
        aovs = out.createNode("Redshift_AOVs", "rsAOVs1")
        aovs.moveToGoodPosition()
        print("Created:", aovs.path())
        
        ### Add AOVs from Json ###
        multiParm = aovs.parm("RS_aov")
        multiParm.set(0)
        file_dir = "/mnt/studio/pipeline/packages/houdini_bcn_tools/1.0.1/bin/bcn/python3.9libs/bcn/aov_base.json"
        data = {}
        with open(file_dir) as outfile:
            data = json.load(outfile)

        blocks = data["aovs"]
        for i in range(len(blocks)):
            multiParm.insertMultiParmInstance(i)

            for name, value in blocks[i].items():
                aovs.parm(name).set(value)