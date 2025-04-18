import re
import numpy as np
import pandas as pd
from typing import Callable

from battetl import logger, Constants, Utils


class Transformer:
    def __init__(
            self,
            timezone: str = None,
            user_transform_test_data: Callable[[
                pd.DataFrame], pd.DataFrame] = None,
            user_transform_cycle_stats: Callable[[
                pd.DataFrame], pd.DataFrame] = None) -> None:
        """
        An interface to transform battery test data to BattETL schema.

        Parameters
        ----------
        timezone : str
            Time zone strings in the IANA Time Zone Database. Used to convert to unix timestamp
            in seconds. Default 'America/Los_Angeles'.
        user_transform_test_data : Callable[[pd.DataFrame], pd.DataFrame], optional
            A user defined function to transform test data. The function should take a pandas.DataFrame
            as input and return a pandas.DataFrame as output.
        user_transform_cycle_stats : Callable[[pd.DataFrame], pd.DataFrame], optional
            A user defined function to transform cycle stats. The function should take a pandas.DataFrame
            as input and return a pandas.DataFrame as output.
        """
        # Default 'America/Los_Angeles'.
        self.timezone = timezone if timezone else Constants.DEFAULT_TIME_ZONE
        self.user_transform_test_data = user_transform_test_data
        self.user_transform_cycle_stats = user_transform_cycle_stats
        if self.user_transform_test_data:
            logger.info('User defined transform_test_data function found')
        if self.user_transform_cycle_stats:
            logger.info('User defined transform_cycle_stats function found')

        self.test_data = pd.DataFrame()
        self.cycle_stats = pd.DataFrame()

    def transform_test_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms test data to conform to BattETL naming and data conventions

        Parameters
        ----------
        data : pandas.DataFrame
            The input DataFrame
        schedule_steps : dict
            A dictionary containing lists of charge (key->'chg'), discharge (key->'dsg'), and 
            rest (key->'rst') steps from the schedule used to generate the data. Used to calculate
            cycle level statistics (e.g. CV charge time.)

        Returns
        -------
        df : pandas.DataFrame
            The transformed output DataFrame
        """
        logger.info('Transform test data')

        df = data.copy()
        df = Utils.drop_unnamed_columns(df)

        cycleMake, dataType = Utils.get_cycle_make(df.columns)
        logger.info(f'Cycle make: {cycleMake}. Data type: {dataType}')

        if cycleMake == Constants.MAKE_ARBIN and dataType == Constants.DATA_TYPE_TEST_DATA:
            df = self.__transform_arbin_test_data(df)

        if cycleMake == Constants.MAKE_MACCOR and dataType == Constants.DATA_TYPE_TEST_DATA:
            df = self.__transform_maccor_test_data(df)

        # Apply user defined transformation
        if self.user_transform_test_data:
            df = self.user_transform_test_data(df)

        self.test_data = df
        return df

    def transform_cycle_stats(self, data: pd.DataFrame):
        """
        Transforms cycle stats to conform to BattETL naming and data conventions

        Parameters
        ----------
        data : pandas.DataFrame
            The input DataFrame

        Returns
        -------
        df : pandas.DataFrame
            The transformed output DataFrame
        """
        logger.info('Transform cycle stats')

        df = data.copy()
        df = Utils.drop_unnamed_columns(df)

        cycleMake, dataType = Utils.get_cycle_make(df.columns)
        logger.info(f'cycle make: {cycleMake}, data type: {dataType}')

        if cycleMake == Constants.MAKE_ARBIN and dataType == Constants.DATA_TYPE_CYCLE_STATS:
            df = self.__transform_arbin_cycle_stats(df)

        if cycleMake == Constants.MAKE_MACCOR and dataType == Constants.DATA_TYPE_CYCLE_STATS:
            df = self.__transform_maccor_cycle_stats(df)

        # Apply user defined transformation
        if self.user_transform_cycle_stats:
            df = self.user_transform_cycle_stats(df)

        self.cycle_stats = df
        return df

    def __transform_arbin_test_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms Arbin test data to conform to BattETL naming and data conventions
        1. Rename columns
        2. Convert to milli
        3. Convert datetime
        4. Convert data type
        5. Sort data

        Parameters
        ----------
        df : pandas.DataFrame
            The input DataFrame

        Returns
        -------
        df : pandas.DataFrame
            The transformed output DataFrame
        """
        df = Utils.rename_df_columns(
            df, Constants.COLUMNS_MAPPING_ARBIN_TEST_DATA)
        df = Utils.convert_to_milli(df)
        df = self.__convert_datetime_unixtime(df)
        df = self.__convert_data_type(df)
        df = Utils.sort_dataframe(df, ['unixtime_s', 'step'])

        return df

    def __transform_arbin_cycle_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms Arbin cycle stats to conform to BattETL naming and data conventions
        1. Rename columns
        2. Convert to milli
        3. Convert data type
        4. Sort data

        Parameters
        ----------
        df : pandas.DataFrame
            The input DataFrame

        Returns
        -------
        df : pandas.DataFrame
            The transformed output DataFrame
        """
        df = Utils.rename_df_columns(
            df, Constants.COLUMNS_MAPPING_ARBIN_CYCLE_STATS)
        df = Utils.convert_to_milli(df)
        df = self.__convert_data_type(df)
        df = Utils.sort_dataframe(df, ['cycle'])

        return df

    def __transform_maccor_test_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms Maccor test data to conform to BattETL naming and data conventions
        1. Rename columns
        2. Convert to milli
        3. Convert datetime
        4. Convert data type
        5. Sort data

        Parameters
        ----------
        df : pandas.DataFrame
            The input DataFrame

        Returns
        -------
        df : pandas.DataFrame
            The transformed output DataFrame
        """
        df = Utils.rename_df_columns(
            df, Constants.COLUMNS_MAPPING_MACCOR_TEST_DATA)
        df = Utils.convert_to_milli(df)
        df = self.__convert_datetime_unixtime(df)
        df = self.__convert_data_type(df)

        if 'test_time_s' in df.columns and len(df) > 0 and self.__timedelta_validation_check(df['test_time_s'][0]):
            df = Utils.convert_timedelta_to_seconds(df, 'test_time_s')
        if 'step_time_s' in df.columns and len(df) > 0 and self.__timedelta_validation_check(df['step_time_s'][0]):
            df = Utils.convert_timedelta_to_seconds(df, 'step_time_s')

        df = Utils.sort_dataframe(df, ['unixtime_s', 'step'])

        return df

    def __transform_maccor_cycle_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms Maccor cycle to conform to BattETL naming and data conventions
        1. Rename columns
        2. Convert to milli
        3. Convert data type
        4. Convert test time
        5. Sort data

        Parameters
        ----------
        df : pandas.DataFrame
            The input DataFrame

        Returns
        -------
        df : pandas.DataFrame
            The transformed output DataFrame
        """
        df = Utils.rename_df_columns(
            df, Constants.COLUMNS_MAPPING_MACCOR_CYCLE_STATS)
        df = Utils.convert_to_milli(df)
        df = self.__convert_data_type(df)

        if 'test_time_s' in df.columns and len(df) > 0 and self.__timedelta_validation_check(df['test_time_s'][0]):
            df = Utils.convert_timedelta_to_seconds(df, 'test_time_s')

        df = Utils.sort_dataframe(df, ['cycle'])

        return df

    def __timedelta_validation_check(self, input_string):
        # Check if it is like the format "1d 15:07:52.77" or "1d 15:07:52"
        regex = re.compile(r'\d+d \d+:\d+:\d+(\.\d+)?\Z', re.I)
        match = regex.match(str(input_string))
        return bool(match)

    def __convert_datetime_unixtime(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert datetime to UTC format and add unixtime_s column

        Parameters
        ----------
        df : pandas.DataFrame
            The input DataFrame

        Returns
        -------
        df : pandas.DataFrame
            The transformed output DataFrame
        """
        logger.info('Convert datetime and add unixtime_s')

        df = Utils.convert_datetime(df, 'recorded_datetime', self.timezone)

        # Convert to unix timestamp
        df['unixtime_s'] = df['recorded_datetime'].astype(np.int64) // 10 ** 9

        return df

    def __convert_data_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert some data types if needed

        Parameters
        ----------
        df : pandas.DataFrame
            The input DataFrame

        Returns
        -------
        df : pandas.DataFrame
            The transformed output DataFrame
        """
        # Change the datatype to save on memory
        if 'cycle' in df.columns:
            logger.info('Convert column `cycle` to uint16')
            df['cycle'] = df['cycle'].astype('uint16')
        if 'stop' in df.columns:
            logger.info('Convert column `step` to uint8')
            df['step'] = df['step'].astype('uint8')

        return df

    def __harmonize_capacity(self, df: pd.DataFrame, steps: dict) -> pd.DataFrame:
        """
        Harmonizes capacity/energy values across cyclers by creating four new columns: `charge_capacity_mah`, 
        `charge_energy_mwh`, `discharge_capacity_mah`, and `discharge_energy_mwh`. These columns only report 
        capacity/energy values during corresponding charge or discharge steps. Otherwise, they will be 
        `NaN`. The original capacity/energy reading is preserved in `cycler_charge_capacity_mah` or 
        `cycler_charge_energy_mwh` column, where `cycler` is replaced with the name of the cycler manufacturer.

        Parameters
        ----------
        df : pd.DataFrame
            A pandas DataFrame containing data for single battery cycle.
        steps : dict
            A dictionary containing lists of charge (key->'chg'), discharge (key->'dsg'), and rest (key->'rst') steps.

        Returns
        -------
        df : pd.DataFrame
            A pandas DataFrame with harmonized capacity/energy values across cyclers.
        """

        if 'maccor_capacity_mah' in df:
            df['charge_capacity_mah'] = df[df.step.isin(
                steps['chg'])].maccor_capacity_mah
            df['discharge_capacity_mah'] = df[df.step.isin(
                steps['dsg'])].maccor_capacity_mah
        if 'maccor_energy_mwh' in df:
            df['charge_energy_mwh'] = df[df.step.isin(
                steps['chg'])].maccor_energy_mwh
            df['discharge_energy_mwh'] = df[df.step.isin(
                steps['dsg'])].maccor_energy_mwh
            # log rows and columns that be modified
            logger.debug(
                f'Harmonized capacity/energy values for Maccor cyclers. Modified {len(df)} rows and 4 columns.')
            logger.debug(
                'Added columns: charge_capacity_mah, charge_energy_mwh, discharge_capacity_mah, discharge_energy_mwh')
        elif 'arbin_charge_capacity_mah' in df:
            df['charge_capacity_mah'] = df[df.step.isin(
                steps['chg'])].arbin_charge_capacity_mah
            df['charge_energy_mwh'] = df[df.step.isin(
                steps['chg'])].arbin_charge_energy_mwh
            df['discharge_capacity_mah'] = df[df.step.isin(
                steps['dsg'])].arbin_discharge_capacity_mah
            df['discharge_energy_mwh'] = df[df.step.isin(
                steps['dsg'])].arbin_discharge_energy_mwh
            logger.debug(
                f'Harmonized capacity/energy values for Arbin cyclers. Modified {len(df)} rows and 4 columns.')
            logger.debug(
                'Added columns: charge_capacity_mah, charge_energy_mwh, discharge_capacity_mah, discharge_energy_mwh')
        else:
            logger.warning("No capacity columns were found to refactor!")

        return df

    def calc_cycle_stats(self, steps: dict, cv_voltage_thresh_mv: float):
        """
        Calculates various charge and discharge statistics at the cycle level. Note this function 
        can only be run after self.test_data exists

        Parameters
        ----------
        steps : dict
            A dictionary containing lists of charge (key->'chg'), discharge (key->'dsg'), and 
            rest (key->'rst') steps.
        cv_voltage_thresh_mv : float
            The the voltage threshold in milli-volts above which charge is considered to be constant voltage.

        Returns
        -------
        stats : dict
            A dictionary containing various charge and discharge stats.
        """
        logger.debug(
            f'Calculating cycle statistics with cv_voltage_thresh_mv: {cv_voltage_thresh_mv}')

        if self.test_data.empty:
            logger.error("Cannot run `calc_cycle_stats()` without test_data!")
            return {}

        self.test_data = self.__harmonize_capacity(self.test_data, steps)

        # DataFrame where we will hold calculated cycle statistics for all cycles
        df_calced_stats = pd.DataFrame(columns=['cycle'])

        for cycle in range(self.test_data.cycle.head(1).item(), self.test_data.cycle.tail(1).item()+1):

            cycle_data = self.test_data[self.test_data.cycle == cycle]
            if cycle_data.empty:
                logger.info("No cycle data for cycle " + str(cycle))
                continue

            # Calculate various charge and discharge cycle statistics.
            stats = {'cycle': cycle}

            charge_metrics = self.__calc_charge_stats(
                cycle_data, steps['chg'], cv_voltage_thresh_mv)
            stats.update(charge_metrics)

            discharge_metrics = self.__calc_discharge_stats(
                cycle_data, steps['dsg'])
            stats.update(discharge_metrics)

            # Calculate coulombic efficiency from the charge and discharge stats.
            if (('calculated_charge_capacity_mah' not in stats) or
                    ('calculated_discharge_capacity_mah' not in stats) or
                    (stats['calculated_charge_capacity_mah'] == 0)):
                ce = float("nan")
                logger.info(
                    "Unable to calculate coulombic efficiency for cycle " + str(cycle))
            else:
                ce = (discharge_metrics['calculated_discharge_capacity_mah']
                      / charge_metrics['calculated_charge_capacity_mah'])
            stats.update({'coulombic_efficiency': ce})

            # Append the cycle statistics from this cycle to our cumulative DataFrame for all cycles.
            df_calced_stats = pd.concat(
                [df_calced_stats, pd.DataFrame(stats, index=[0])], axis=0)

        if self.cycle_stats.empty:
            self.cycle_stats = df_calced_stats
        else:
            self.cycle_stats = self.cycle_stats.join(
                df_calced_stats.set_index('cycle'), on='cycle')

        return self.cycle_stats

    def __calc_charge_stats(self, cycle_data: pd.DataFrame, charge_steps: list, cv_voltage_thresh_mv: float) -> dict:
        """
        Calculates various charge stats for a single cycle of data.

        Parameters
        ----------
        cycle_data : pd.DataFrame
            A dataframe containing data for single battery cycle.
        charge_steps : list
            List of charge steps from the cycler schedule.
        cv_voltage_thresh_mv : float
            The the voltage threshold in milli-volts above which charge is considered to be constant voltage.

        Returns
        -------
        stats : dict
            A dictionary containing various charge stats.
        """
        logger.debug(
            f'Calculating charge statistics with cv_voltage_thresh_mv: {cv_voltage_thresh_mv}')
        stats = {}

        # Define charge data to be where the step is a charge step.
        chg_data = cycle_data[cycle_data.step.isin(charge_steps)]
        if len(chg_data) < 2:
            logger.info("No charge data for cycle " +
                        str(cycle_data.cycle.iloc[0]))
            return stats

        ez_df = self.__ez_calc_df(
            chg_data, charge_steps, 'charge', cv_voltage_thresh_mv)

        stats['calculated_charge_capacity_mah'] = ez_df['charge_capacity_mah'].iloc[-1]
        stats['calculated_charge_energy_mwh'] = ez_df['charge_energy_mwh'].iloc[-1]
        stats['calculated_charge_time_s'] = ez_df['ellapsed_time_s'].iloc[-1]

        stats['calculated_cc_charge_time_s'] = ez_df.cc_time_s.sum()
        stats['calculated_cv_charge_time_s'] = ez_df.cv_time_s.sum()
        stats['calculated_cc_capacity_mah'] = ez_df.cc_capacity_mah.sum()
        stats['calculated_cv_capacity_mah'] = ez_df.cv_capacity_mah.sum()

        # Calculate 50%/80% charge time & capacity.
        eighty_percent_cap_mah = stats['calculated_charge_capacity_mah'] * 0.8
        fifty_percent_cap_mah = stats['calculated_charge_capacity_mah'] * 0.5
        try:
            eighty_percent_cap_time_s = (ez_df[ez_df.charge_capacity_mah > eighty_percent_cap_mah].ellapsed_time_s.iloc[0]
                                         - ez_df.ellapsed_time_s.iloc[0])
            half_percent_cap_time_s = (ez_df[ez_df.charge_capacity_mah > fifty_percent_cap_mah].ellapsed_time_s.iloc[0]
                                       - ez_df.ellapsed_time_s.iloc[0])
        except:
            eighty_percent_cap_time_s = float('nan')
            half_percent_cap_time_s = float('nan')
            logger.warning(
                f'Incomplete charge data for cycle {cycle_data.cycle.iloc[0]}')

        stats['calculated_fifty_percent_charge_time_s'] = half_percent_cap_time_s
        stats['calculated_eighty_percent_charge_time_s'] = eighty_percent_cap_time_s

        return stats

    def __calc_discharge_stats(self, cycle_data: pd.DataFrame, discharge_steps: list) -> dict:
        """
        Calculates various discharge stats for a single cycle of data.

        Parameters
        ----------
        cycle_data : pd.DataFrame
            A dataframe containing data for single battery cycle.
        discharge_steps : list
            List of discharge steps from the cycler schedule.

        Returns
        -------
        stats : dict
            A dictionary containing various discharge stats.
        """
        logger.debug('Calculating discharge statistics')
        stats = {}

        # Define discharge data to be where the step is a discharge step.
        dsg_data = cycle_data[cycle_data.step.isin(discharge_steps)]
        if len(dsg_data) < 2:
            logger.info("No discharge data for cycle " +
                        str(cycle_data.cycle.iloc[0]))
            return stats

        ez_df = self.__ez_calc_df(dsg_data, discharge_steps, 'discharge')

        stats['calculated_discharge_capacity_mah'] = ez_df['discharge_capacity_mah'].iloc[-1]
        stats['calculated_discharge_energy_mwh'] = ez_df['discharge_energy_mwh'].iloc[-1]
        stats['calculated_discharge_time_s'] = ez_df['ellapsed_time_s'].iloc[-1]

        return stats

    def __ez_calc_df(self, cycle_df: pd.DataFrame, steps: list, step_type: str, cv_voltage_thresh_mv=None) -> tuple:
        """
        Creates a DataFrame we can easily use to calculate cycle statistics.

        Modifies test_data to cummulative capacity in cases where capacity is reset at each step.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame use to calculate cumulative capacity.
        steps : list
            A list of the steps to calculate cumulative capacity for. 
        step_type : str
            Either 'charge' or 'discharge' depending on what type of steps we are calculating for.
        cv_voltage_thresh_mv : float
            The voltage threshold in mV above which charge is considered to be constant voltage.    

        Returns
        -------
        ez_df: pd.DataFrame
            Dataframe containing values filtered to charge steps with cumulative capacity
            and ellapsed time calculated.
        """
        logger.debug(f'Calculating cumulative {step_type} capacity')

        time_col = 'ellapsed_time_s'
        volt_col = 'voltage_mv'
        cc_time = 'cc_time_s'
        cv_time = 'cv_time_s'
        cc_cap = 'cc_capacity_mah'
        cv_cap = 'cv_capacity_mah'
        if step_type == 'charge':
            cap_col = 'charge_capacity_mah'
            eng_col = 'charge_energy_mwh'
        elif step_type == 'discharge':
            cap_col = 'discharge_capacity_mah'
            eng_col = 'discharge_energy_mwh'
        else:
            logger.error(f'Unknown step type {step_type}!')
            return pd.DataFrame()

        ez_df = pd.DataFrame(
            columns=[time_col, volt_col, cap_col, eng_col, cc_time, cv_time, cc_cap, cv_cap])

        # Iterate through each charge step to calculate cumulative capacity

        for i, step in enumerate(steps):

            step_slice = cycle_df[cycle_df.step == step]
            step_df = pd.DataFrame(
                columns=[time_col, volt_col, cap_col, eng_col, cc_time, cv_time, cc_cap, cv_cap])

            if step_slice.empty:
                continue

            if ez_df.empty:
                ez_df[time_col] = step_slice['test_time_s'] - \
                    step_slice['test_time_s'].iloc[0]
                ez_df[volt_col] = step_slice['voltage_mv']
                ez_df[eng_col] = step_slice[eng_col] - \
                    step_slice[eng_col].iloc[0]
                ez_df[cap_col] = step_slice[cap_col] - \
                    step_slice[cap_col].iloc[0]
                if step_type == 'charge':
                    # if ez_df is empty, we're at beginning of a cycle and cap/step time should be reset to zero
                    # TODO: add documentation for this
                    delta_time = step_slice['step_time_s'] - \
                        step_slice['step_time_s'].shift(1, fill_value=0)
                    ez_df[cc_time] = np.where(
                        step_slice[volt_col] < cv_voltage_thresh_mv, delta_time, 0)
                    ez_df[cv_time] = np.where(
                        step_slice[volt_col] >= cv_voltage_thresh_mv, delta_time, 0)
                    delta_cap = step_slice[cap_col] - \
                        step_slice[cap_col].shift(1, fill_value=0)
                    ez_df[cc_cap] = np.where(
                        step_slice[volt_col] < cv_voltage_thresh_mv, delta_cap, 0)
                    ez_df[cv_cap] = np.where(
                        step_slice[volt_col] >= cv_voltage_thresh_mv, delta_cap, 0)
                # TODO: corner case of ICT will still need above logic for discharge
                elif step_type == 'discharge':
                    ez_df[[cc_time, cc_cap, cv_time, cv_cap]] = np.nan
            else:
                # This catches if capacity was reset after each step. Modifies test_data DF in place.
                if step_slice[cap_col].iloc[0] < ez_df[cap_col].iloc[-1]:
                    current_cycle = cycle_df.cycle.iloc[0]
                    self.test_data.loc[self.test_data.cycle == current_cycle,
                                       self.test_data.step == step, cap_col] += ez_df[cap_col]
                    self.test_data.loc[self.test_data.cycle == current_cycle,
                                       self.test_data.step == step, eng_col] += ez_df[eng_col]
                if not ez_df.empty:
                    # keeps running time across steps. ignoring time between steps
                    step_df[time_col] = (
                        step_slice['test_time_s'] - step_slice['test_time_s'].iloc[0]) + ez_df[time_col].iloc[-1]
                # step_slice is updated with above updates to test_data because it's a slice, not copy, of test_data
                step_df[volt_col] = step_slice[volt_col]
                step_df[cap_col] = step_slice[cap_col]
                step_df[eng_col] = step_slice[eng_col]
                if step_type == 'charge':
                    # calculate the delta time/cap for each step, sum the deltas in calc_stats() to get cycle time/cap
                    delta_time = step_slice['step_time_s'] - \
                        step_slice['step_time_s'].shift(1, fill_value=0)
                    step_df[cc_time] = np.where(
                        step_slice[volt_col] < cv_voltage_thresh_mv, delta_time, 0)
                    step_df[cv_time] = np.where(
                        step_slice[volt_col] >= cv_voltage_thresh_mv, delta_time, 0)
                    delta_cap = step_slice[cap_col] - step_slice[cap_col].shift(
                        1, fill_value=ez_df[cap_col].iloc[-1])
                    step_df[cc_cap] = np.where(
                        step_slice[volt_col] < cv_voltage_thresh_mv, delta_cap, 0)
                    step_df[cv_cap] = np.where(
                        step_slice[volt_col] >= cv_voltage_thresh_mv, delta_cap, 0)
                elif step_type == 'discharge':
                    step_df[[cc_time, cc_cap, cv_time, cv_cap]] = np.nan
                ez_df = pd.concat([ez_df, step_df])
        logger.debug(f'Finished calculating cumulative {step_type} capacity')
        return ez_df
