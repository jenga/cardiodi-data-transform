import pandas as pd
import itertools
import numpy as np
import os
from tqdm import tqdm
import click

tqdm.pandas()

def read_data(input_file):
    return pd.read_csv(input_file, 
                 header=None,
                 names=[
                     'Procedure.Number',
                     'DataExport.Procedure',
                     'DataExport.Patient',
                     'DataExport.Exams',
                     'DataExport.DiagnosticReport',
                     'Indications',
                     'Protocols',
                     'Sequences',
                     'DataExport.Measurements',
                     'Findings',
                     'SegmentalFunctionCode.LV',
                     'SegmentalFunctionCode.RV',
                     'DataExport.SegmentalFibrosis.LV',
                     'SegmentalFibrosisPresence.RV',
                     'DataExport.RVInsertionFibrosis',
                     'DataExport.SegmentalStress.LV',
                     'SegmentalEdemaPresence.LV',
                     'SegmentalEdemaPresence.RV'
                 ])

def expand_fibrosis(row):
    base = 'SegmentalFibrosis.LV'
    for s in range(1,18):
        seg = row['{}.{}'.format(base, s)]
        fields = seg.split("^^")
        row['{}.{}.{}'.format(base, s, 'NoReflow')] = fields[0]
        row['{}.{}.{}'.format(base, s, 'Subendo')] = fields[1].split("$$")
        row['{}.{}.{}'.format(base, s, 'Subepi')] = fields[2].split("$$")
        row['{}.{}.{}'.format(base, s, 'Diffuse')] = fields[3].split("$$")
        row['{}.{}.{}'.format(base, s, 'Patchy')] = fields[4].split("$$")
        row['{}.{}.{}'.format(base, s, 'Striae')] = fields[5].split("$$")
    return row

def boolean_mask(item, item_list):
    if isinstance(item_list, list):
        return item in item_list
    else:
        return False

def boolean_df(item_lists, unique_items):
# Create empty dict
    bool_dict = {}
    
    # Loop through all the tags
    for item in unique_items:
        if not isinstance(item, str) and np.isnan(item):
            continue
        # Apply boolean mask
        bool_dict[item] = item_lists.apply(lambda x: boolean_mask(item, x))
            
    # Return the results as a dataframe
    return pd.DataFrame(bool_dict)

@click.command()
@click.option('--input_file')
@click.option('--output_file')
def convert(input_file, output_file):
    print('Starting conversion...')
    print('Reading data...')
    df = read_data(input_file)
    print('Data Read.')
    print('Splitting out data objects...')
    df_procedure_number = df.iloc[:,0]
    df_procedure = df.iloc[:,1].str.split(pat="\|\|", expand=True)
    df_patient = df.iloc[:,2].str.split(pat="\|\|", expand=True)
    df_exam = df.iloc[:,3].str.split(pat="\|\|", expand=True)
    df_diagnostic_report = df.iloc[:,4].str.split(pat="\|\|", expand=True)
    df_segmental_function_lv = df.iloc[:,10].str.split(pat="\|\|", expand=True)
    df_segmental_function_rv = df.iloc[:,11].str.split(pat="\|\|", expand=True)
    df_segmental_fibrosis_lv = df.iloc[:,12].str.split(pat="\|\|", expand=True)
    df_segmental_fibrosis_rv = df.iloc[:,13].str.split(pat="\|\|", expand=True)
    df_rv_insertion_fibrosis = df.iloc[:,14].str.split(pat="\|\|", expand=True)
    df_segmental_stress = df.iloc[:,15].str.split(pat="\|\|", expand=True)
    df_segmental_edema_lv = df.iloc[:,16].str.split(pat="\|\|", expand=True)
    df_segmental_edema_rv = df.iloc[:,17].str.split(pat="\|\|", expand=True)
    df_findings = df.iloc[:,9].str.split(pat="\|\|")
    print('Data objects extracted.')
    print('Labelling columns...')
    df_procedure_number.columns = ['Procedure.Number']
    df_procedure.columns = [
        'Procedure.StatusCode',
        'Procedure.StudyTypeCode',
        'Procedure.ScheduledDateTime',
        'Encounter.PatientTypeCode',
        'Procedure.CreatedDateTime',
        'Procedure.ImageQuality',
        'Procedure.HeartRhythm'
    ]
    df_patient.columns = [
        'PatientFile.ID',
        'PatientFile.ReferenceID',
        'PatientFile.Identifier',
        'PatientRecord.BirthSex',
        'PatientRecord.DOB'
    ]
    df_diagnostic_report.columns = [
        'DiagnosticReport.StatusCode',
        'DiagnosticReport.PrimaryReader',
        'DiagnosticReport.AssistingReaders',
        'DiagnosticReport.OverallImpressions'
    ]
    df_segmental_function_lv.columns = ['SegmentalFunction.LV.{}'.format(s) for s in range(1,18)]
    df_segmental_function_rv.columns = ['SegmentalFunction.RV.{}'.format(s) for s in range(1,13)]
    df_segmental_fibrosis_lv.columns = ['SegmentalFibrosis.LV.{}'.format(s) for s in range(1,18)]
    df_segmental_fibrosis_rv.columns = ['SegmentalFibrosis.RV.{}'.format(s) for s in range(1,13)]
    df_rv_insertion_fibrosis.columns = ['RVInsertionFibrosis.{}'.format(s) for s in range(1,5)]
    df_segmental_stress.columns = ['SegmentalStress.LV.{}'.format(s) for s in range(1,18)]
    df_segmental_edema_lv.columns = ['SegmentalEdemaPresence.LV.{}'.format(s) for s in range(1,18)]
    df_segmental_edema_rv.columns = ['SegmentalEdemaPresence.RV.{}'.format(s) for s in range(1,13)]
    print('Columns labelled.')
    print('Expanding fibrosis data...')

    df_segmental_fibrosis_lv = df_segmental_fibrosis_lv.progress_apply(expand_fibrosis, axis=1)
    df_segmental_fibrosis_lv.drop(['SegmentalFibrosis.LV.{}'.format(s) for s in range(1,18)], axis=1, inplace=True)

    print('Fibrosis data expanded.')
    print('Expanding measurement data...')

    df_measurements = df.iloc[:,[0,8]]
    df_measurements.columns = ['Procedure.Number', 'DataExport.Measurement']

    measurements = {}
    for i, ms in tqdm(df_measurements.iterrows()):
        m_list = ms['DataExport.Measurement'].split("||")
        for m in m_list:
            fields = m.split("^^")
            if fields[0] not in measurements.keys():
                measurements[fields[0]] = [None] * i
            measurements[fields[0]].append(fields[1:])
        for k, l in measurements.items():
            if len(l) < (i + 1):
                measurements[k].append(None)
    df_measurements = pd.concat([df_measurements, pd.DataFrame(measurements)], axis=1)
    df_measurements.drop(columns=['Procedure.Number'], inplace=True)
    print('Measurement data expanded.')
    print('Expanding findings data...')
    df_findings = boolean_df(df_findings, df_findings.explode().unique())
    columns = sorted(df_findings.columns)
    df_findings = df_findings[columns]
    print('Findings data expanded.')
    print('Exporting to csv...')
    final_df = pd.concat([
        df, 
        df_procedure, 
        df_patient, 
        df_diagnostic_report, 
        df_measurements, 
        df_findings, 
        df_segmental_function_lv, 
        df_segmental_function_rv, 
        df_segmental_fibrosis_lv, 
        df_segmental_fibrosis_rv, 
        df_rv_insertion_fibrosis, 
        df_segmental_stress, 
        df_segmental_edema_lv, 
        df_segmental_edema_rv], axis=1)
    final_df.replace({'null': pd.NA}, inplace=True)
    final_df.to_csv(output_file, index=False)
    print('CSV Exported.')
    print('Conversion Completed.')

if __name__ == '__main__':
    convert()