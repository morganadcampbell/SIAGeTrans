from math import prod


class BargainSolver:
    @staticmethod
    def bargain(S : list[list[int]], dParams : list, U : list) -> tuple[list[int],float]:
        """
        @staticmethod
        Given a list of possible combinations of values to x (S) and a list of disagreement (d), 
        returns the combination that maximizes the payoff (ui).
        N(S,d) = argmax(x in S) Pi(1,n) (ui(xi) - di)
        Return: returns x that maximizes the payoff and its payoff
        """
        bestx = S[0]
        bestpayoff = float('-inf')
        dmin = min([eval(U[i].replace('x\'', str(dParams[i]))) for i in range(len(dParams))])
        for x in S:
            payoff = prod([eval(U[i].replace('x\'', str(x[i]))) - dmin for i in range(len(x))])
            if payoff > bestpayoff:
                bestpayoff = payoff
                bestx = x
        return bestx,bestpayoff
    
    @staticmethod
    def getS(phases, min, max, total, bias = dict()):
        """
        @staticmethod
        Generates a list of all possible combinations of times for phases in a 
        cycle given minimum, maximum and total times.
        Filter it by bias, if defined.

        Ex.: phases = 3, min = 1, max = 3, total = 4
             output: [[1, 1, 2], [1, 2, 1], [2, 1, 1]]
             if bias = {0 : 1}
             output: [[1, 1, 2], [1, 2, 1]]
        """
        def comb(phases, min, max):
            if phases == 1: return [[i] for i in range(min, max+1)]
            else: return[[i, *y] for i in range(min, max+1) for y in comb(phases-1, min, max)]
        return list(filter(lambda x : sum(x) == total and all([x[k] == v for k,v in bias.items()]), comb(phases, min, max)))

    
    @staticmethod
    def utilityFunction(fixedParams : dict, phaseParams : list[dict]) -> list: 
        """
        @staticmethod
        Given a list of necessary params, returns a payoff function to be used in the bargain process for each phase
        The utility function Q for a phase i is given in terms of t_g (time of green light).

        Q_i(t_g) = w * Femrg_i * Ffld_i * (<queued vehicles> + <arriving vehicles>) 
                    + Fwea_i * (<queued pedestrians> + <arriving pedestrians>) 
                    - w * <departing vehicles> - <departing vehicles>

        Return: returns the utility function for each phase given the appropriate parameters
        """
        # (eq1) basic equation: w * (<queued vehicles> + <arriving vehicles>) + <queued pedestrians> + <arriving pedestrians> - w * <departing vehicles> - <departing vehicles>
        # equation = "- ( ( {w} * ( sum({VCL_l}) + sum([ ({t_c} - x') * y for y in {DeltaVCLin_l}]) ) ) " + \
        #             "+ sum({PDT_j}) + sum([ ({t_c} - x') * y for y in {DeltaPDTin_j}]) " + \
        #             "- ( {w} * sum([ x' * y for y in {DeltaVCLout_l}]) ) " + \
        #             "- sum([ x' * y for y in {DeltaPDTout_j}]) )"
        # (eq2) equation with weather priorization: w * (<queued vehicles> + <arriving vehicles>) + Fwea_i * (<queued pedestrians> + <arriving pedestrians>) - w * <departing vehicles> - <departing vehicles>
        # equation = "- ( ( {w} * ( sum({VCL_l}) + sum([ ({t_c} - x') * y for y in {DeltaVCLin_l}]) ) ) " + \
        #             "+ ( (1 + ({Pwea} * abs({Tcur} - (({Tmax} + {Tmin})/2) ) / (({Tmax} - {Tmin})/2) ) ) * ( sum({PDT_j}) + sum([ ({t_c} - x') * y for y in {DeltaPDTin_j}]) ) )" + \
        #             "- ( {w} * sum([ x' * y for y in {DeltaVCLout_l}]) ) " + \
        #             "- sum([ x' * y for y in {DeltaPDTout_j}]) )"
        # (eq3) equation with weather and flooding priorization: w *  ( (Ffld_i * <queued vehicles>) + <arriving vehicles>) + Fwea_i * (<queued pedestrians> + <arriving pedestrians>) - w * <departing vehicles> - <departing vehicles>
        equation = "- ( ( {w} * ( ( (1 + ({Pfld} * {VCLfld_i} / max({VCLfld_tot}, 1) ) ) * sum({VCL_l}) ) + sum([ ({t_c} - x') * y for y in {DeltaVCLin_l}]) ) ) " + \
                    "+ ( (1 + ({Pwea} * abs({Tcur} - (({Tmax} + {Tmin})/2) ) / (({Tmax} - {Tmin})/2) ) ) * ( sum({PDT_j}) + sum([ ({t_c} - x') * y for y in {DeltaPDTin_j}]) ) )" + \
                    "- ( {w} * sum([ x' * y for y in {DeltaVCLout_l}]) ) " + \
                    "- sum([ x' * y for y in {DeltaPDTout_j}]) )"
        functions = []
        for paramsCombination in phaseParams:
            functions.append(equation.format(**paramsCombination, **fixedParams))
        return functions
    
    @staticmethod
    def getBestSetup(fixedParams : dict, phaseParams : list[dict], bias = dict()) -> list:
        """
        Returns the best possible output given appropriate parameters.

        Needed Params:
            - fixedParams:
                - "phases": number of cycle's phases
                - "minimumTime": minimum accepted time for a phase
                - "maximumTime": maximum accepted time for a phase
                - "waitingTime": waiting time between phases (default = 1s)
                - "d": desagreement value for each phase (default = minimumTime)
                - "w": persons per car
                - "Tcur": current temperature
                - "Tmax": max teperature
                - "Tmin": min temperature
                - "Pemrg": priority vehicles priorization factor
                - "Pfld": flooding priorization factor
                - "Pwea": weather priorization factor
                - "t_c": cycle's total time (sum of green time + waiting time (1s) for each phase)
            - phaseParams:
                - "PDT_j": queued pedestrian in sidewalk (j) of a phase (i)
                - "VCL_l": queued vehicles per roadsection (l) in a phase (i)
                - "DeltaVCLin_l": roadsection (l) arriving vehicles rate (per second) in a phase (i)
                - "DeltaPDTin_j": sideway (j) arriving pedestrian rate (per second) in a phase (i)
                - "DeltaVCLout_l": roadsection (l) departing vehicles rate (per second) in a phase (i)
                - "DeltaPDTout_j": sideway (j) departing pedestrian rate (per second) in a phase (i)
                - "VCLemrg_i": number of prioritary vehicles in a phase (i)
                - "VCLfld_i": number of vehicles in a flooding in a phase (i)
                - "VCLemrg_tot": total number of prioritary vehicles in the intersection
                - "VCLfld_tot": total number of vehicles in a flooding in the intersection
        
        Bias is optional; it maps a phase to a fixed result.
        Return: list with best times for each phase of a cycle
        """
        S = BargainSolver.getS(fixedParams["phases"], fixedParams["minimumTime"], fixedParams["maximumTime"], fixedParams["t_c"] - (fixedParams["waitingTime"] * fixedParams["phases"]), bias)
        dParams = fixedParams["dParams"]
        functions = BargainSolver.utilityFunction(fixedParams, phaseParams)
        bestx,bestpayoff = BargainSolver.bargain(S, dParams, functions)
        return bestx






## testing ##########################################################################################
if __name__ == '__main__':
    
    phaseParams = [dict(), dict(), dict()]

    phaseParams[0]["PDT_j"] = [1,1] # queued pedestrian in sidewalk (j) of a phase (i)
    phaseParams[0]["VCL_l"] = [5,10] # queued vehicles per roadsection (l) in a phase (i)
    phaseParams[0]["DeltaVCLin_l"] = [10,10] # roadsection (l) arriving vehicles rate (per second) in a phase (i)
    phaseParams[0]["DeltaPDTin_j"] = [1,1] # sideway (j) arriving pedestrian rate (per second) in a phase (i)
    phaseParams[0]["DeltaVCLout_l"] = [1,2] # roadsection (l) departing vehicles rate (per second) in a phase (i)
    phaseParams[0]["DeltaPDTout_j"] = [1,1] # sideway (j) departing pedestrian rate (per second) in a phase (i)
    phaseParams[0]["VCLemrg_i"] = 0 # number of prioritary vehicles in a phase (i)
    phaseParams[0]["VCLfld_i"] = 0 # number of vehicles in a flooding in a phase (i)
    phaseParams[0]["VCLemrg_tot"] = 0 # total number of prioritary vehicles in the intersection
    phaseParams[0]["VCLfld_tot"] = 0 # total number of vehicles in a flooding in the intersection


    phaseParams[1]["PDT_j"] = [1,1] # queued pedestrian in sidewalk (j) of a phase (i)
    phaseParams[1]["VCL_l"] = [2,2] # queued vehicles per roadsection (l) in a phase (i)
    phaseParams[1]["DeltaVCLin_l"] = [3,5] # roadsection (l) arriving vehicles rate (per second) in a phase (i)
    phaseParams[1]["DeltaPDTin_j"] = [1,1] # sideway (j) arriving pedestrian rate (per second) in a phase (i)
    phaseParams[1]["DeltaVCLout_l"] = [2,1] # roadsection (l) departing vehicles rate (per second) in a phase (i)
    phaseParams[1]["DeltaPDTout_j"] = [1,1] # sideway (j) departing pedestrian rate (per second) in a phase (i)
    phaseParams[1]["VCLemrg_i"] = 0 # number of prioritary vehicles in a phase (i)
    phaseParams[1]["VCLfld_i"] = 0 # number of vehicles in a flooding in a phase (i)
    phaseParams[1]["VCLemrg_tot"] = 0 # total number of prioritary vehicles in the intersection
    phaseParams[1]["VCLfld_tot"] = 0 # total number of vehicles in a flooding in the intersection


    phaseParams[2]["PDT_j"] = [1,1] # queued pedestrian in sidewalk (j) of a phase (i)
    phaseParams[2]["VCL_l"] = [5] # queued vehicles per roadsection (l) in a phase (i)
    phaseParams[2]["DeltaVCLin_l"] = [1] # roadsection (l) arriving vehicles rate (per second) in a phase (i)
    phaseParams[2]["DeltaPDTin_j"] = [1,1] # sideway (j) arriving pedestrian rate (per second) in a phase (i)
    phaseParams[2]["DeltaVCLout_l"] = [2] # roadsection (l) departing vehicles rate (per second) in a phase (i)
    phaseParams[2]["DeltaPDTout_j"] = [1,1] # sideway (j) departing pedestrian rate (per second) in a phase (i)
    phaseParams[2]["VCLemrg_i"] = 0 # number of prioritary vehicles in a phase (i)
    phaseParams[2]["VCLfld_i"] = 0 # number of vehicles in a flooding in a phase (i)
    phaseParams[2]["VCLemrg_tot"] = 0 # total number of prioritary vehicles in the intersection
    phaseParams[2]["VCLfld_tot"] = 0 # total number of vehicles in a flooding in the intersection


    fixedParams = dict()
    fixedParams["phases"] = 3 # number of cycle's phases
    fixedParams["minimumTime"] = 10 # minimum accepted time for a phase
    fixedParams["maximumTime"] = 40 # maximum accepted time for a phase
    fixedParams["waitingTime"] = 5 # waiting time between phases (default = 1s)
    fixedParams["dParams"] = [10, 10, 10] # desagreement value for each phase (default = minimumTime)
    fixedParams["w"] = 1.34 # persons per car
    fixedParams["Tcur"] = 10 # current temperature
    fixedParams["Tmax"] = 30 # max teperature
    fixedParams["Tmin"] = 10 # min temperature
    fixedParams["Pemrg"] = 2 # priority vehicles priorization factor
    fixedParams["Pfld"] = 2 # flooding priorization factor
    fixedParams["Pwea"] = 2 # weather priorization factor
    fixedParams["t_c"] = 70 # cycle's total time (sum of green time + waiting time (1s) for each phase)

    bestx = BargainSolver.getBestSetup(fixedParams, phaseParams)
    print(bestx)