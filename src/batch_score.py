# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import sys
import os
import argparse 

import joblib
import pandas as pd
from azureml.core.model import Model
from azureml.core import Dataset
import json
from utils import get_dataset, retrieve_workspace

def preprocessing(X):
    """
    Create Week_number from WeekStarting
    Drop two unnecessary columns: WeekStarting, Revenue
    """
    X['WeekStarting'] = pd.to_datetime(X['WeekStarting'])
    X['week_number'] = X['WeekStarting'].apply(lambda x: x.strftime("%U"))
    # Drop 'WeekStarting','Revenue' columns if it exist
    X = X.drop(['WeekStarting','Revenue','Quantity'], axis = 1, errors ='ignore')
    return X

    
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset-name',dest='dataset_name',default='oj_sales_ds', type=str, help='')
    parser.add_argument('--output-dir',dest='output_idr',default='./', type=str, help='')
    parser.add_argument('--forecast-name',dest='forecast_name',default='forecast.csv', type=str, help='')
    parser.add_argument('--model-name',dest='model_name',default='sale_regression.pkl', type=str, help='')
    # parser.add_argument('--model_file_name', default='sale_regression.pkl', type=str, help='')
    args, _ = parser.parse_known_args()

    ws = retrieve_workspace()
    dataset = Dataset.get_by_name(ws,args.dataset_name)
    data = dataset.to_pandas_dataframe()
    model_path = None

    try:
        model_path = Model.get_model_path(model_name = args.model_name)
    except Exception as e:
        print('Model not found in cache. Trying to download locally')

    if model_path is None:
        try:
            model_container = Model(ws,name = args.model_name)
            model_path = model_container.download()
        except Exception as e:
            print('Error while trying to download model')
            print(e)
            sys.exit(-1)

    with open(model_path,'rb') as file_model:
        model = joblib.load(file_model)

    data = preprocessing(data)
    data['forecast'] = model.predict(data)

    # with open(args.output_dir + args.forecast_name,'w') as file_forecast:
    file_forecast = args.output_dir + args.forecast_name

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    data.to_csv(file_forecast,index=False)

if __name__ == "__main__":
    main()
