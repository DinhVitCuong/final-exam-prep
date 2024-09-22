import pandas as pd 
from sklearn.ensemble import RandomForestRegressor
import json
from chart_drawing2 import DrawTotal, DrawChap

class prepThreshold:
    def __init__(self, path, subject):
        self.path = path
        self.subject = subject
        self.dic = dic = {
            'chapter': [],
            'difficulty': [],
            'date': [],
            'accuracy': []
        }
        self.load_and_save()
    def load_and_save(self):
        # Load total results
        with open(f"{self.subject}_total_results.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            num = len(data)
            for i in range(num):
                test = DrawTotal(self.subject, None, "total", i, "specific")
                chap_difficulty_percentile = test.difficult_percentile_per_chap()
                for chap, dic_diff in chap_difficulty_percentile.items():
                    for type1, acuc in dic_diff.items():
                        self.dic['chapter'].append(chap)
                        self.dic['difficulty'].append(type1)
                        self.dic['date'].append(data[i]['completion_time'])
                        self.dic['accuracy'].append(acuc)

        # Load chapter results
        with open(f"{self.subject}_chapter_results.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            num = len(data)
            for i in range(num):
                test = DrawChap(self.subject, None, "chapter", i, "specific")
                chap_difficulty_percentile = test.difficult_percentile_per_chap()
                for chap, dic_diff in chap_difficulty_percentile.items():
                    for type1, acuc in dic_diff.items():
                        self.dic['chapter'].append(chap)
                        self.dic['difficulty'].append(type1)
                        self.dic['date'].append(data[i]['completion_time'])
                        self.dic['accuracy'].append(acuc)

        # Create DataFrame
        df = pd.DataFrame(self.dic)

        # Convert date to datetime format
        df["date"] = pd.to_datetime(df["date"])

        # Extract useful features from the date
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day_of_year'] = df['date'].dt.dayofyear

        # Drop the original 'date' column if it's no longer needed
        df = df.drop(columns=['date'])
        df.to_csv(self.path, index=False)
    


class predictThreshold:
    def __init__(self, path, predict_type, subject):
        self.X_train = None
        self.predict_type = predict_type
        self.max_chap = None
        self.path = path
        self.subject = subject
        self.X_test = None
        self.date = None
        self.load_data()
        self.predict()
    def load_data(self):
        # load data
        data = pd.read_csv(self.path)
        self.X_train = data.drop(columns=['accuracy'])
        self.y_train = data['accuracy']
        print(f"{self.subject}_{self.predict_type}_results.json",)
        # Load JSON data with error handling
        try:
            with open(f"{self.subject}_{self.predict_type}_results.json", "r", encoding="utf-8") as file:
                json_data = json.load(file)
                if not json_data:
                    raise ValueError("JSON data is empty")
                self.max_chap = json_data[-1]['chapter']
                self.date = pd.to_datetime(json_data[-1]['completion_time'])
        except FileNotFoundError:
            raise FileNotFoundError(f"The file {self.subject}_{self.predict_type}_results.json was not found.")
        except json.JSONDecodeError:
            raise ValueError(f"The file {self.subject}_{self.predict_type}_results.json contains invalid JSON.")
        except ValueError as e:
            raise e

    def create_x_test(self):
        # Extract year, month, day_of_year from the date
        year = self.date.year
        month = self.date.month
        day_of_year = self.date.dayofyear

        # create x_test
        if self.predict_type == "total":
            self.X_test = {
                'chapter': [],
                'difficulty': [],
                'year': [],
                'month': [],
                'day_of_year': [],
            }
            for i in range(1, self.max_chap + 1):
                for j in range(1, 5):
                    self.X_test['chapter'].append(i)
                    self.X_test['difficulty'].append(j)
                    self.X_test['year'].append(year)
                    self.X_test['month'].append(month)
                    self.X_test['day_of_year'].append(day_of_year)
        else:
            self.X_test = {
                'chapter': [self.max_chap, self.max_chap, self.max_chap, self.max_chap],
                'difficulty': [1, 2, 3, 4],
                'year': [year, year, year, year],
                'month': [month, month, month, month],
                'day_of_year': [day_of_year, day_of_year, day_of_year, day_of_year],
            }

        self.X_test = pd.DataFrame(self.X_test)

    def predict(self):
        # predict
        model = RandomForestRegressor()
        model.fit(self.X_train, self.y_train)
        self.create_x_test()
        self.y_pred = model.predict(self.X_test)
        return self.y_pred
    
    def predicted_data(self):
        # concat with self.X_test
        self.X_test['accuracy'] = self.y_pred
        self.X_test.to_csv(f"{self.subject}_{self.predict_type}_threshold.csv", index=False)
        return self.X_test
    

# cai nay chay truoc roi moi qua prompt

# predict_type = "chapter" # ["chapter", "total"]
# path = "threshold_data.csv"
# subject = "T"
# prep = prepThreshold(path, subject)
# predict = predictThreshold(path, predict_type, subject)
# print(predict.predicted_data())





