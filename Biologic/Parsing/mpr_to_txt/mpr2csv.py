'''
Script for converting Biologic .mpr files to other file formats. The default
output format is csv.
'''
import argparse
import pandas as pd
from galvani import BioLogic

output_cmd = {
    'csv': lambda df, f: pd.DataFrame.to_csv(df, f, index=False),
    'txt': lambda df, f: pd.DataFrame.to_csv(df, f, index=False, sep='\t'),
    'excel': lambda df, f: pd.DataFrame.to_excel(df, f, index=False),
    'feather': pd.DataFrame.to_feather,
    'hdf': lambda df, f: pd.DataFrame.to_hdf(df, f, key='Index'),
    'json': pd.DataFrame.to_json,
    'parquet': pd.DataFrame.to_parquet,
    'pickle': pd.DataFrame.to_pickle,
    'stata': pd.DataFrame.to_stata
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('in_file', help='input file', type=str)
    parser.add_argument('out_file', help='output file', type=str)
    parser.add_argument('-f', '--format', default='csv',
                        choices=output_cmd.keys())
    args = parser.parse_args()

    parsed_mpr = BioLogic.MPRfile(args.in_file)
    print("Start date of experiement: {}\nEnd date of experiment: {}".format(
        parsed_mpr.startdate, parsed_mpr.enddate))

    df = pd.DataFrame(parsed_mpr.data)
    output_cmd[args.format](df, args.out_file)

    print(f"Output written to: {args.out_file}")


if __name__ == '__main__':
    main()
