# To generate System Under Test(SUT) descriptions automatically

This script will automatically run lscpu parser and QAIC tool parser. To run the script,

```
export SUT=<SUT_NAME>

axs byquery auto_desc_gen,sut=${SUT}
```

If you are running with non-QAIC devices, you will need to add a tool detector and a tool parser to the workflow. 

### Step `[1]`: Add a Tool Detector 

As an example we have added a QAIC tool Detector [here](https://github.com/krai/axs2qaic-dev/blob/qaic-util-tool/qaic_util_tool_detector/data_axs.json)

### Step `[2]`: Add a Tool Parser

As an example we have added a QAIC tool Parser [here](https://github.com/krai/axs2qaic-dev/tree/qaic-util-tool/qaic_util_parser)

### Step `[3]`: Add as an parent entry

Next, we will need to add `sut_desc_gen` as a parent entry of the SUT entry. As an example, `dl385_q8_std` [here](https://github.com/krai/axs2qaic-dev/blob/cb87dc1ebeb67a112229bab08daf2c43e310a4f9/qaic_sut_collection/dl385_q8_std/data_axs.json#L8)

### Step `[4]`: Add producer rule

Next, add producer rule to the existing SUT. As an example, we have added the producer rule to `dl385_q8_std` [here](https://github.com/krai/axs2qaic-dev/blob/cb87dc1ebeb67a112229bab08daf2c43e310a4f9/qaic_sut_collection/dl385_q8_std/data_axs.json#L37)

