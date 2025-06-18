from math import prod


class BargainSolver:
    @staticmethod
    def bargain(S : list[list[int]], d : list, U : list) -> tuple[list[int],float]:
        """
        @staticmethod
        Given a list of possible combinations of values to x (S) and a list of disagreement (d), 
        returns the combination that maximizes the payoff (ui).
        N(S,d) = argmax(x in S) Pi(1,n) (ui(xi) - di)
        Return: returns x that maximizes the payoff and its payoff
        """
        bestx = S[0]
        bestpayoff = float('-inf')
        for x in S:
            payoff = prod([eval(U[i].replace('x', str(x[i]))) - d[i] for i in range(len(x))])
            if payoff > bestpayoff:
                bestpayoff = payoff
                bestx = x
        return bestx,bestpayoff
    
    @staticmethod
    def getS(phases, min, max, total):
        """
        @staticmethod
        Generates a list of all possible combinations of times for phases in a 
        cycle given minimum, maximum and total times.

        Ex.: phases = 3, min = 1, max = 3, total = 4
             output: [[1, 1, 2], [1, 2, 1], [2, 1, 1]]
        """
        def comb(phases, min, max):
            if phases == 1: return [[i] for i in range(min, max+1)]
            else: return[[i, *y] for i in range(min, max+1) for y in comb(phases-1, min, max)]
        return list(filter(lambda x : sum(x) == total, comb(phases, min, max)))

    
    @staticmethod
    def utilityFunction(fixedParams : dict, phaseParams : list[dict]) -> list: 
        """
        @staticmethod
        Given a list of necessary params, returns a payoff function to be used in the bargain process for each phase
        The utility function Q for a phase i is given in terms of t_g (time of green light).

        Q_i(t_g) = w * Fvip_i * Ffld_i * (<queued vehicles> + <arriving vehicles>) 
                    + Fwea_i * (<queued pedestrians> + <arriving pedestrians>) 
                    - w * <departing vehicles> - <departing vehicles>

        Return: returns the utility function for each phase given the appropriate parameters
        """
        functions = []
        for params in phaseParams:
            w = fixedParams["w"]
            Fvip_i = 1 + fixedParams['Pvip'] * (params['VCLvip_i']/(params['VCLvip_tot']+1)) # 1 + Pvip * ( (SUM{l in i}(VCLvip_l))/(VCLvip_tot + 1) )
            Ffld_i = 1 + fixedParams['Pfld'] * (params['VCLfld_i']/(params['VCLfld_tot']+1)) # 1 + Pfld * ( (SUM{l in i}(VCLfld_l))/(VCLfld_tot + 1) )
            Fwea_i = 1  + fixedParams['Pwea'] * ( abs(fixedParams['Tcur'] - ((fixedParams['Tmax'] + fixedParams['Tmin'])/2))/( (fixedParams['Tmax'] - fixedParams['Tmin'])/2 ) ) # 1 + Pwea * ( ABS(Tcur - ((Tmax + Tmin)/2))/( (Tmax - Tmin)/2 ) )
            QueuedVehicles = str(sum((1 - params['INDcls_l'][i]) * params['VCL_l'][i] for i in range(len(params['VCL_l'])))) # SUM{l in i}( (1 - INDcls_l) * VCL_l)
            ArrivingVehicles = str(sum((1 - params['INDcls_l'][i]) * params['DeltaVCLin_l'][i] for i in range(len(params['DeltaVCLin_l'])))) + ' * (' + str(fixedParams['t_c']) + ' - x)' # SUM{l in i}( (1 - INDcls_l) * DeltaVCLin_l ) * (t_c - t_g)
            QueuedPedestrians = str(sum(params["PDT_j"])) # PDT_i = SUM{j in i}(PDT_j)
            ArrivingPedestrians = str(sum(params['DeltaPDTin_j'])) + ' * (' + str(fixedParams['t_c']) + ' - x)' # SUM{j in i}( DeltaPDTin_j ) * (t_c - t_g)
            DepartingVehicles = str(sum(params['DeltaVCLout_l'])) + ' * x' # SUM{l in i}(DeltaVCLout_l) * t_g
            DepartingPedestrians = str(sum(params['DeltaPDTout_j'])) + ' * x' # SUM{j in i}(DeltaPDTout_j) * t_g
            functions.append('(' + str(w * Fvip_i * Ffld_i) + ' * ' + '(' + QueuedVehicles + ' + ' + ArrivingVehicles + '))' + \
                                        ' + (' + str(Fwea_i) + ' * ' + '(' + QueuedPedestrians + ' + ' + ArrivingPedestrians + '))' + \
                                        ' - ' + '(' + str(w) + ' * ' + DepartingVehicles + ') - (' + DepartingPedestrians + ')')
        return functions
    
    @staticmethod
    def getBestSetup(fixedParams : dict, phaseParams : list[dict]) -> list:
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
                - "Pvip": priority vehicles priorization factor
                - "Pfld": flooding priorization factor
                - "Pwea": weather priorization factor
                - "t_c": cycle's total time (sum of green time + waiting time (1s) for each phase)
            - phaseParams:
                - "PDT_j": queued pedestrian in sidewalk (j) of a phase (i)
                - "INDcls_l": Index of closure for a roadsection (l) in a phase (i)
                - "VCL_l": queued vehicles per roadsection (l) in a phase (i)
                - "DeltaVCLin_l": roadsection (l) arriving vehicles rate (per second) in a phase (i)
                - "DeltaPDTin_j": sideway (j) arriving pedestrian rate (per second) in a phase (i)
                - "DeltaVCLout_l": roadsection (l) departing vehicles rate (per second) in a phase (i)
                - "DeltaPDTout_j": sideway (j) departing pedestrian rate (per second) in a phase (i)
                - "VCLvip_i": number of prioritary vehicles in a phase (i)
                - "VCLfld_i": number of vehicles in a flooding in a phase (i)
                - "VCLvip_tot": total number of prioritary vehicles in the intersection
                - "VCLfld_tot": total number of vehicles in a flooding in the intersection

        Return: list with best times for each phase of a cycle
        """
        S = BargainSolver.getS(fixedParams["phases"], fixedParams["minimumTime"], fixedParams["maximumTime"], fixedParams["t_c"] - (fixedParams["waitingTime"] * fixedParams["phases"]))
        d = fixedParams["d"]
        functions = BargainSolver.utilityFunction(fixedParams, phaseParams)
        bestx,bestpayoff = BargainSolver.bargain(S, d, functions)
        return bestx

if __name__ == '__main__':

    phaseParams = [dict(), dict(), dict()]

    phaseParams[0]["PDT_j"] = [1,1] # queued pedestrian in sidewalk (j) of a phase (i)
    phaseParams[0]["INDcls_l"] = [0,0] # index of closure for a roadsection (l) in a phase (i)
    phaseParams[0]["VCL_l"] = [5,10] # queued vehicles per roadsection (l) in a phase (i)
    phaseParams[0]["DeltaVCLin_l"] = [10,10] # roadsection (l) arriving vehicles rate (per second) in a phase (i)
    phaseParams[0]["DeltaPDTin_j"] = [1,1] # sideway (j) arriving pedestrian rate (per second) in a phase (i)
    phaseParams[0]["DeltaVCLout_l"] = [1,2] # roadsection (l) departing vehicles rate (per second) in a phase (i)
    phaseParams[0]["DeltaPDTout_j"] = [1,1] # sideway (j) departing pedestrian rate (per second) in a phase (i)
    phaseParams[0]["VCLvip_i"] = 0 # number of prioritary vehicles in a phase (i)
    phaseParams[0]["VCLfld_i"] = 0 # number of vehicles in a flooding in a phase (i)
    phaseParams[0]["VCLvip_tot"] = 0 # total number of prioritary vehicles in the intersection
    phaseParams[0]["VCLfld_tot"] = 0 # total number of vehicles in a flooding in the intersection


    phaseParams[1]["PDT_j"] = [1,1] # queued pedestrian in sidewalk (j) of a phase (i)
    phaseParams[1]["INDcls_l"] = [0,1] # index of closure for a roadsection (l) in a phase (i)
    phaseParams[1]["VCL_l"] = [2,2] # queued vehicles per roadsection (l) in a phase (i)
    phaseParams[1]["DeltaVCLin_l"] = [3,5] # roadsection (l) arriving vehicles rate (per second) in a phase (i)
    phaseParams[1]["DeltaPDTin_j"] = [1,1] # sideway (j) arriving pedestrian rate (per second) in a phase (i)
    phaseParams[1]["DeltaVCLout_l"] = [2,1] # roadsection (l) departing vehicles rate (per second) in a phase (i)
    phaseParams[1]["DeltaPDTout_j"] = [1,1] # sideway (j) departing pedestrian rate (per second) in a phase (i)
    phaseParams[1]["VCLvip_i"] = 0 # number of prioritary vehicles in a phase (i)
    phaseParams[1]["VCLfld_i"] = 0 # number of vehicles in a flooding in a phase (i)
    phaseParams[1]["VCLvip_tot"] = 0 # total number of prioritary vehicles in the intersection
    phaseParams[1]["VCLfld_tot"] = 0 # total number of vehicles in a flooding in the intersection


    phaseParams[2]["PDT_j"] = [1,1] # queued pedestrian in sidewalk (j) of a phase (i)
    phaseParams[2]["INDcls_l"] = [0] # index of closure for a roadsection (l) in a phase (i)
    phaseParams[2]["VCL_l"] = [5] # queued vehicles per roadsection (l) in a phase (i)
    phaseParams[2]["DeltaVCLin_l"] = [1] # roadsection (l) arriving vehicles rate (per second) in a phase (i)
    phaseParams[2]["DeltaPDTin_j"] = [1,1] # sideway (j) arriving pedestrian rate (per second) in a phase (i)
    phaseParams[2]["DeltaVCLout_l"] = [2] # roadsection (l) departing vehicles rate (per second) in a phase (i)
    phaseParams[2]["DeltaPDTout_j"] = [1,1] # sideway (j) departing pedestrian rate (per second) in a phase (i)
    phaseParams[2]["VCLvip_i"] = 0 # number of prioritary vehicles in a phase (i)
    phaseParams[2]["VCLfld_i"] = 0 # number of vehicles in a flooding in a phase (i)
    phaseParams[2]["VCLvip_tot"] = 0 # total number of prioritary vehicles in the intersection
    phaseParams[2]["VCLfld_tot"] = 0 # total number of vehicles in a flooding in the intersection


    fixedParams = dict()
    fixedParams["phases"] = 3 # number of cycle's phases
    fixedParams["minimumTime"] = 10 # minimum accepted time for a phase
    fixedParams["maximumTime"] = 40 # maximum accepted time for a phase
    fixedParams["waitingTime"] = 5 # waiting time between phases (default = 1s)
    fixedParams["d"] = [10, 10, 10] # desagreement value for each phase (default = minimumTime)
    fixedParams["w"] = 1.34 # persons per car
    fixedParams["Tcur"] = 10 # current temperature
    fixedParams["Tmax"] = 30 # max teperature
    fixedParams["Tmin"] = 10 # min temperature
    fixedParams["Pvip"] = 2 # priority vehicles priorization factor
    fixedParams["Pfld"] = 2 # flooding priorization factor
    fixedParams["Pwea"] = 2 # weather priorization factor
    fixedParams["t_c"] = 70 # cycle's total time (sum of green time + waiting time (1s) for each phase)

    bestx = BargainSolver.getBestSetup(fixedParams, phaseParams)
    print(bestx)