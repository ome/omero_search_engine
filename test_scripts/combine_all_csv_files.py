import pandas as pd
import glob

idr0043 = "/data/data_dump/projects/idr0043-uhlen-humanproteinatlas/experimentA"
idr0013 = "/data/data_dump/screens/idr0013-neumann-mitocheck/screenA"
files_list = glob.glob("%s/*.csv" % idr0043)
print(len(files_list))

df_list = []
# append all files together
for file in files_list:
    df_ = pd.read_csv(file)
    df_list.append(df_)
all_df = pd.concat(df_list)
all_df.to_csv("file_name", index=False)
