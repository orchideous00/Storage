# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

class GIRR:
    def __init__(self):
        self.__tenor = [0.25, 0.5, 1, 2, 3, 5, 10, 15, 20, 30]  # MAR 21.8
        self.__riskweight = [0.017, 0.017, 0.016, 0.013, 0.012, 0.011, 0.011, 0.011, 0.011, 0.011]  # MAR 21.42

        self.__rw_round = True

        self.__corr_scenario_list = ["H", "M", "L"]
        self.__MCorrBucketIn = pd.DataFrame(0, index=self.__tenor, columns=self.__tenor, dtype='float')
        self.__calc_corr_bucket_in_normal()
        self.__HCorrBucketIn = self.__MCorrBucketIn.apply(np.vectorize(lambda x: np.min((1.25*x, 1))))  # MAR 21.6 (2)
        self.__LCorrBucketIn = self.__MCorrBucketIn.apply(np.vectorize(lambda x: np.max((0.75*x, 2*x-1))))  # MAR 21.6 (3)
        self.__CorrBucketInDict = {"H": self.__HCorrBucketIn, "M": self.__MCorrBucketIn, "L": self.__LCorrBucketIn}

        self.__HCorrBucketOut = None
        self.__MCorrBucketOut = None
        self.__LCorrBucketOut = None
        self.__CorrBUcketInOut = {"H": self.__HCorrBucketOut, "M": self.__MCorrBucketOut, "L": self.__LCorrBucketOut}

        self.__RiskWeight = pd.DataFrame(self.__riskweight, index=self.__tenor, columns=['weight'])

        self.__MajCur = ["EUR", "USD", "GBP", "AUD", "JPY", "SEK", "CAD", "KRW"]
        self.__MajCurAdjRatio = np.sqrt(2)

        self.__GIRRDeltaCVRTData = None
        self.__GIRRDeltaData = None
        self.__GIRRDeltaDataTarget = None
        self.__GIRRDeltaCurveSum = None
        self.__GIRRDeltaCurveSumAdj = None
        self.__GIRRCVRTData = None

        self.__BucketInKbDict = None
        self.__BucketOutSbDict = None

        self.__GIRRDeltaMatHigh = None
        self.__GIRRDeltaMatMedium = None
        self.__GIRRDeltaMatLow = None
        self.__GIRRDeltaMatDict = {"H": self.__GIRRDeltaMatHigh, "M": self.__GIRRDeltaMatMedium, "L": self.__GIRRDeltaMatLow}

        self.__GIRRDeltaRiskHigh = None
        self.__GIRRDeltaRiskMedium = None
        self.__GIRRDeltaRiskLow = None
        self.__GIRRDeltaRiskDict = {"H": self.__GIRRDeltaRiskHigh, "M": self.__GIRRDeltaRiskMedium, "L": self.__GIRRDeltaRiskLow}

        self.__GIRRDeltaRisk = None

    def set_rw_round(self, t): self.__rw_round = t

    def __calc_corr_bucket_in_normal(self):
        for tk, row in self.__MCorrBucketIn.iterrows():
            for ti, v in row.iteritems():
                self.__MCorrBucketIn.loc[tk, ti] = self.__calc_corr_bucket_in(tk, ti)

    @staticmethod
    def __calc_corr_bucket_in(tk, ti): return np.max((0.4, np.exp(-0.03 * np.abs(tk - ti) / np.min((tk, ti)))))  # MAR 21.46

    def get_corr_bucket_in(self, corr_case): return self.__CorrBucketInDict[corr_case].copy()

    def set_girr_delta_cvrt_data(self, file_loc, file_name): self.__GIRRDeltaCVRTData = pd.read_csv(file_loc + file_name)

    def set_eval_date(self, evaldate):
        self.__GIRRDeltaDataTarget = self.__GIRRDeltaCVRTData.loc[self.__GIRRDeltaCVRTData["evaldate"] == int(evaldate), :]

    def get_girr_delta_data_target(self): return self.__GIRRDeltaDataTarget.copy()

    def calc_girr(self):
        self.calc_girr_delta()

    def calc_girr_delta(self):
        self.__GIRRDeltaCurveSum = self.__GIRRDeltaDataTarget.groupby(["ccy", "curve", "tenor"]).sum().reset_index()
        self.__GIRRDeltaCurveSum.pop("evaldate")

        self.__calc_girr_delta_weighted_sum()

        self.__calc_girr_delta_corr_bucket_out()
        self.__BucketInKbDict = {}
        self.__BucketOutSbDict = {}
        for s in self.__corr_scenario_list:
            self.__calc_girr_delta_scenario(s)

    def get_girr_delta_curve_sum(self): return self.__GIRRDeltaCurveSum.copy()

    def __calc_girr_delta_weighted_sum(self):
        self.__GIRRDeltaCurveSumAdj = self.__GIRRDeltaCurveSum.copy()
        self.__GIRRDeltaCurveSumAdj["AdjRatio"] = 1
        self.__GIRRDeltaCurveSumAdj.loc[self.__GIRRDeltaCurveSumAdj.ccy.isin(self.__MajCur), "AdjRatio"] /= self.__MajCurAdjRatio  # MAR 21.44
        self.__GIRRDeltaCurveSumAdj["rw"] = self.__GIRRDeltaCurveSumAdj.tenor.map(self.__RiskWeight["weight"])
        self.__GIRRDeltaCurveSumAdj["rw"] *= self.__GIRRDeltaCurveSumAdj["AdjRatio"]

        self.__GIRRDeltaCurveSumAdj["rw"] = self.__GIRRDeltaCurveSumAdj["rw"].round(4) if self.__rw_round else self.__GIRRDeltaCurveSumAdj["rw"]

        self.__GIRRDeltaCurveSumAdj["sens_adj"] = self.__GIRRDeltaCurveSumAdj["sens"] * self.__GIRRDeltaCurveSumAdj["rw"]

    def get_girr_delta_weighted_sum(self): return self.__GIRRDeltaCurveSumAdj.copy()

    def __calc_girr_delta_corr_bucket_out(self):
        self.__MCorrBucketOut = pd.DataFrame(0.5, index=self.__GIRRDeltaCurveSumAdj.ccy.unique(), columns=self.__GIRRDeltaCurveSumAdj.ccy.unique(), dtype='float')
        np.fill_diagonal(self.__MCorrBucketOut.values, 1)

        self.__HCorrBucketOut = self.__MCorrBucketOut.applymap(lambda x: np.min((1.25*x, 1)))  # 필요없음
        self.__LCorrBucketOut = self.__MCorrBucketOut.applymap(lambda x: np.max((2*x-1, 0.75*x)))  # 필요없음

        self.__CorrBucketOutDict = {"H": self.__HCorrBucketOut, "M": self.__MCorrBucketOut, "L": self.__LCorrBucketOut}

    def get_corr_bucket_out(self, corr_case): return self.__CorrBucketOutDict[corr_case].copy()

    def __calc_girr_delta_scenario(self, corr_case):
        gamma_bc = self.__CorrBucketOutDict[corr_case].copy()
        sbsc = self.__GIRRDeltaCurveSumAdj.groupby(['ccy'])['sens_adj'].sum()
        self.__GIRRDeltaMatDict[corr_case] = gamma_bc.mul(sbsc, axis=0).mul(sbsc, axis=1)

        self.__BucketOutSbDict[corr_case] = sbsc

        kb = pd.Series(0, self.__GIRRDeltaCurveSumAdj.ccy.unique(), dtype='float')
#        corrki = self.__CorrBucketInDict[corr_case].copy()
        corrki = self.__CorrBucketInDict["M"].copy()
        for ccy, v in kb.iteritems():
            s = self.__GIRRDeltaCurveSumAdj.loc[self.__GIRRDeltaCurveSumAdj.ccy == ccy, :].groupby(['curve', 'tenor'])['sens_adj'].sum()
            df = pd.DataFrame(0, index=s.index, columns=s.index)

            for i, row in df.iterrows():
                curve_i, tenor_i = i
                for j, val in row.iteritems():
                    curve_j, tenor_j = j
                    if i == j:
                        rho = 1
                    elif (tenor_i == tenor_j) & (curve_i != curve_j):
                        rho = 0.999
                    elif (tenor_i != tenor_j) & (curve_i == curve_j):
                        rho = corrki.loc[tenor_i, tenor_j]
                    else:
                        rho = corrki.loc[tenor_i, tenor_j]*0.999

                    if corr_case == "H":
                        rho = np.min((1.25*rho, 1))
                    elif corr_case == "L":
                        rho = np.max((2*rho-1, 0.75*rho))

                    df.loc[i, j] = s[i] * s[j] * rho

            kb[ccy] = np.sqrt(df.to_numpy().sum())

        self.__BucketInKbDict[corr_case] = kb

        np.fill_diagonal(self.__GIRRDeltaMatDict[corr_case].values, kb**2)

        self.__GIRRDeltaRiskDict[corr_case] = np.sqrt(self.__GIRRDeltaMatDict[corr_case].to_numpy().sum())

    def get_girr_kb_bucket_in(self, corr_case): return self.__BucketInKbDict[corr_case]  # 사실상 필요없음

    def get_girr_sb_bucket_out(self, corr_case): return self.__BucketOutSbDict[corr_case]

    def get_girr_delta_mat(self, corr_case): return self.__GIRRDeltaMatDict[corr_case]

    def get_girr_risk_sce(self, corr_case): return self.__GIRRDeltaRiskDict[corr_case]
