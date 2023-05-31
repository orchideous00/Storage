# -*- coding: utf-8 -*-
import sys
import pandas as pd
import GIRR

pd.options.display.max_columns = None
pd.set_option('display.float_format', '{:.5f}'.format)

scenario_list = ["H", "M", "L"]

if __name__ == '__main__':
    args = sys.argv[1:]
    girr = GIRR.GIRR()

    file_loc = ""
    girr_delta_file_name = "GIRR_DELTA_DATA_SAMPLE.csv"

    girr.set_girr_delta_cvrt_data(file_loc, girr_delta_file_name)

    girr_result = pd.DataFrame(0, index=args, columns=scenario_list)

    for d in args:
        girr.set_eval_date(d)
        girr.calc_girr()
        for sce in scenario_list:
            print("\nCorr Scenario: {0}".format(sce))
            print("\nKb")
            print(girr.get_girr_kb_bucket_in(sce))
            print("\nSbSc")
            print(girr.get_girr_sb_bucket_out(sce))
            print("\nDelta Matrix")
            print(girr.get_girr_delta_mat(sce))
            girr_result.loc[d, sce] = girr.get_girr_risk_sce(sce)
            print("\nRC: {:,.2f}".format(girr.get_girr_risk_sce(sce)))

    print("\nResult")
    print(girr_result)

print("done")
