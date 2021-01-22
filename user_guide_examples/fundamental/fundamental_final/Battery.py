# -*- coding: utf-8 -*-
"""
Created on 8/31/2020

This is a simple battery value federate that models the physics of an EV
battery as it is being charged. The federate receives a voltage signal
representing the voltage applied to the charging terminals of the battery
and based on its internally modeled SOC, calculates the current draw of
the battery and sends it back to the EV federate. Note that this SOC should
be considered the true SOC of the battery which may be different than the
SOC modeled by the charger

This model differs from the Combo Example in that it creates federates and
registers them with the HELICS API.

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import helics as h
import logging
import numpy as np
import matplotlib.pyplot as plt


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)




def destroy_federate(fed):
    '''
    As part of ending a HELICS co-simulation it is good housekeeping to
    formally destroy a federate. Doing so informs the rest of the
    federation that it is no longer a part of the co-simulation and they
    should proceed without it (if applicable). Generally this is done
    when the co-simulation is complete and all federates end execution
    at more or less the same wall-clock time.

    :param fed: Federate to be destroyed
    :return: (none)
    '''
    status = h.helicsFederateFinalize(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()
    logger.info('Federate finalized')

def create_value_federate(fedinitstring,name,period):
    fedinfo = h.helicsCreateFederateInfo()
    # "coreType": "zmq",
    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
    h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)
    # "loglevel": 1,
    h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 1)
    # "period": 60,
    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, period)
    # "uninterruptible": false,
    h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_uninterruptible, False)
    # "terminate_on_error": true,
    h.helicsFederateInfoSetFlagOption(fedinfo, 72, True)
    # "wait_for_current_time_update": true,
    h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_wait_for_current_time_update, True)
    # "name": "Battery",
    fed = h.helicsCreateValueFederate(name, fedinfo)
    return fed

def get_new_battery(numBattery):
    '''
    Using hard-coded probabilities, a distribution of battery of
    fixed battery sizes are generated. The number of batteries is a user
    provided parameter.

    :param numBattery: Number of batteries to generate
    :return
        listOfBatts: List of generated batteries

    '''

    # Probabilities of a new EV having a battery at a given capacity.
    #   The three random values (25,62, 100) are the kWh of the randomly
    #   selected battery.
    size_1 = 0.2
    size_2 = 0.2
    size_3 = 0.6
    listOfBatts = np.random.choice([25,62,100],numBattery,p=[size_1,size_2,
                                                       size_3]).tolist()

    return listOfBatts


if __name__ == "__main__":
    np.random.seed(2622)

    ##########  Registering  federate and configuring with API################
    fedinitstring = " --federates=1"
    name = "Battery"
    period = 60
    fed = create_value_federate(fedinitstring,name,period)
    logger.info(f'Created federate {name}')
    print(f'Created federate {name}')

    num_EVs = 5
    pub_count = num_EVs
    pubid = {}
    for i in range(0,pub_count):
        # "key":"Battery/EV1_current",
        pub_name = f'Battery/EV{i+1}_current'
        pubid[i] = h.helicsFederateRegisterGlobalTypePublication(
                    fed, pub_name, 'double', 'A')
        logger.debug(f'\tRegistered publication---> {pub_name}')

    sub_count = num_EVs
    subid = {}
    for i in range(0,sub_count):
        sub_name = f'Charger/EV{i+1}_voltage'
        subid[i] = h.helicsFederateRegisterSubscription(
                    fed, sub_name, 'V')
        logger.debug(f'\tRegistered subscription---> {sub_name[i]}')

    sub_count = h.helicsFederateGetInputCount(fed)
    logger.debug(f'\tNumber of subscriptions: {sub_count}')
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logger.debug(f'\tNumber of publications: {pub_count}')

    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info('Entered HELICS execution mode')

    hours = 24*7 # one week
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(
                                fed,
                                h.HELICS_PROPERTY_TIME_PERIOD))
    grantedtime = 0

    # Define battery physics as empirical values
    socs = np.array([0, 1])
    effective_R = np.array([8, 150])

    batt_list = get_new_battery(pub_count)

    current_soc = {}
    for i in range (0, pub_count):
        current_soc[i] = (np.random.randint(0,60))/100



    # Data collection lists
    time_sim = []
    current = []
    soc = {}

    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = (grantedtime+update_interval)
        logger.debug(f'Requesting time {requested_time}')
        grantedtime = h.helicsFederateRequestTime (fed, requested_time)
        logger.debug(f'Granted time {grantedtime}')

        for j in range(0,sub_count):
            logger.debug(f'Battery {j+1} time {grantedtime}')

            # Get the applied charging voltage from the EV
            charging_voltage = h.helicsInputGetDouble((subid[j]))
            logger.debug(f'\tReceived voltage {charging_voltage:.2f} from input'
                         f' {h.helicsSubscriptionGetKey(subid[j])}')

            # EV is fully charged and a new EV is moving in
            # This is indicated by the charging removing voltage when it
            #    thinks the EV is full
            if charging_voltage == 0:
                new_batt = get_new_battery(1)
                batt_list[j] = new_batt[0]
                current_soc[j] = (np.random.randint(0,80))/100
                charging_current = 0

            # Calculate charging current and update SOC
            R =  np.interp(current_soc[j], socs, effective_R)
            logger.debug(f'\tEffective R (ohms): {R:.2f}')
            charging_current = charging_voltage / R
            logger.debug(f'\tCharging current (A): {charging_current:.2f}')
            added_energy = (charging_current * charging_voltage * \
                           update_interval/3600) / 1000
            logger.debug(f'\tAdded energy (kWh): {added_energy:.4f}')
            current_soc[j] = current_soc[j] + added_energy / batt_list[j]
            logger.debug(f'\tSOC: {current_soc[j]:.4f}')



            # Publish out charging current
            h.helicsPublicationPublishDouble(pubid[j], charging_current)
            logger.debug(f'\tPublished {pub_name[j]} with value '
                         f'{charging_current:.2f}')

            # Store SOC for later analysis/graphing
            if subid[j] not in soc:
                soc[subid[j]] = []
            soc[subid[j]].append(float(current_soc[j]))

        # Data collection vectors
        time_sim.append(grantedtime)
        current.append(charging_current)



    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)
    # Printing out final results graphs for comparison/diagnostic purposes.
    xaxis = np.array(time_sim)/3600
    y = []
    for key in soc:
        y.append(np.array(soc[key]))

    plt.figure()

    fig, axs = plt.subplots(5, sharex=True, sharey=True)
    fig.suptitle('SOC of each EV Battery')

    axs[0].plot(xaxis, y[0], color='tab:blue', linestyle='-')
    axs[0].set_yticks(np.arange(0,1.25,0.5))
    axs[0].set(ylabel='Batt at\nport 1')
    axs[0].grid(True)

    axs[1].plot(xaxis, y[1], color='tab:blue', linestyle='-')
    axs[1].set(ylabel='Batt a\nport 2')
    axs[1].grid(True)

    axs[2].plot(xaxis, y[2], color='tab:blue', linestyle='-')
    axs[2].set(ylabel='Batt at\nport 3')
    axs[2].grid(True)

    axs[3].plot(xaxis, y[3], color='tab:blue', linestyle='-')
    axs[3].set(ylabel='Batt at\nport 4')
    axs[3].grid(True)

    axs[4].plot(xaxis, y[4], color='tab:blue', linestyle='-')
    axs[4].set(ylabel='Batt at\nport 5')
    axs[4].grid(True)
    plt.xlabel('time (hr)')
    #for ax in axs():
#        ax.label_outer()
    # Saving graph to file
    plt.savefig('fundamental_final_battery_SOCs.png', format='png')

    plt.show()