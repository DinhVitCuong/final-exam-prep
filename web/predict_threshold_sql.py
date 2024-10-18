import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import json
from data_retriever_sql import DrawTotal, DrawChap
from app import create_app, db, login_manager, bcrypt
from models import User, Progress, Test, Universities, QAs, Subject, SubjectCategory

class PrepThreshold:
    def __init__(self, subject, user_id=None):
        self.subject = subject
        self.dic = {
            'chapter': [],
            'difficulty': [],
            'date': [],
            'accuracy': []
        }
        self.user_id = user_id
        self.load_and_save()

    def load_and_save(self):
        # Load total results

        query1 = db.session.query(Test).filter(
            Test.questions.like(f"{self.subject}%")
        )
        query = query1.filter_by(test_type=1, user_id = int(self.user_id)).all()
        num = len(query)
        for i in range(num):
            try:
                test = DrawTotal(self.subject, None, 1, i, self.user_id, "specific")
                chap_difficulty_percentile = test.difficult_percentile_per_chap()
                for chap, dic_diff in chap_difficulty_percentile.items():
                    for type1, acuc in dic_diff.items():
                        self.dic['chapter'].append(chap)
                        self.dic['difficulty'].append(type1)
                        self.dic['date'].append(query[i].time)
                        self.dic['accuracy'].append(acuc)
            except:
                continue
        
        # Repeat the process for another set of data if needed
        
        query = query1.filter_by(test_type=0, user_id = int(self.user_id)).all()
        num = len(query)
        for i in range(num):
            try:
                test = DrawChap(self.subject, None, 0, i, self.user_id, "specific")
                chap_difficulty_percentile = test.difficult_percentile_per_chap()
                for chap, dic_diff in chap_difficulty_percentile.items():
                    for type1, acuc in dic_diff.items():
                        self.dic['chapter'].append(chap)
                        self.dic['difficulty'].append(type1)
                        self.dic['date'].append(query[i].time)
                        self.dic['accuracy'].append(acuc)
            except:
                continue
        
        # Create DataFrame
        df = pd.DataFrame(self.dic)

        # Convert date to datetime format
        df["date"] = pd.to_datetime(df["date"], errors='coerce')

        # Check for any invalid date conversions
        if df['date'].isnull().any():
            raise ValueError("Some date values could not be converted to datetime. Check the input data.")

        # Extract useful features from the date
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day_of_year'] = df['date'].dt.dayofyear

        # Drop the original 'date' column if it's no longer needed
        df = df.drop(columns=['date'])
        return df
        # df.to_csv(self.path, index=False)
from sklearn.exceptions import NotFittedError


class PredictThreshold:
    def __init__(self, predict_type, subject, user_id , max_chap = None):
        self.X_train = None
        self.predict_type = int(predict_type)  # Ensure predict_type is an integer
        self.max_chap = max_chap
        self.user_id = user_id
        self.subject = subject
        self.X_test = None
        self.date = None
        self.load_data()
        self.predict()

    def load_data(self):
        # Load data from CSV
        data = PrepThreshold(self.subject, self.user_id).load_and_save()
        self.X_train = data.drop(columns=['accuracy'])
        self.y_train = data['accuracy']

        # Load JSON data with error handling
        try:
            if self.predict_type == 1:
                query = db.session.query(Test).filter(
                    Test.questions.like(f"{self.subject}%"),
                    Test.test_type.like(self.predict_type),
                    Test.user_id.like(int(self.user_id))
                ).order_by(Test.knowledge).all()
                
                self.max_chap = int(query[-1].knowledge)  # Ensure knowledge is treated as an integer
                self.date = pd.to_datetime(query[-1].time, errors='coerce')  # Ensure the date is parsed correctly
            else:
                query = db.session.query(Test).filter(
                    Test.questions.like(f"{self.subject}%"),
                    Test.test_type.like(self.predict_type),
                    Test.knowledge.like(f"0{self.max_chap}"),
                    Test.user_id.like(int(self.user_id)) 
                ).all()
                self.date = pd.to_datetime(query[-1].time, errors='coerce')
            if pd.isnull(self.date):
                raise ValueError("Invalid date format encountered in the database.")
        except IndexError:
            raise IndexError("No matching test records found.")
        except FileNotFoundError:
            raise FileNotFoundError(f"The file {self.subject}_{self.predict_type}_results.json was not found.")
        except json.JSONDecodeError:
            raise ValueError(f"The file {self.subject}_{self.predict_type}_results.json contains invalid JSON.")
        except ValueError as e:
            raise e

    def create_x_test(self):
        # Extract year, month, day_of_year from the date
        if self.date is None:
            raise ValueError("Date is not set. Cannot create X_test without a valid date.")
        year = self.date.year
        month = self.date.month
        day_of_year = self.date.dayofyear

        # Create X_test based on predict_type
        if self.predict_type == 1:
            self.X_test = {
                'chapter': [],
                'difficulty': [],
                'year': [],
                'month': [],
                'day_of_year': [],
            }
            for i in range(1, self.max_chap + 1):
                for j in range(0, 4):
                    self.X_test['chapter'].append(i)
                    self.X_test['difficulty'].append(j)
                    self.X_test['year'].append(year)
                    self.X_test['month'].append(month)
                    self.X_test['day_of_year'].append(day_of_year)
        else:
            self.X_test = {
                'chapter': [self.max_chap] * 4,
                'difficulty': list(range(4)),
                'year': [year] * 4,
                'month': [month] * 4,
                'day_of_year': [day_of_year] * 4,
            }

        self.X_test = pd.DataFrame(self.X_test)

    def predict(self):
        # Check if X_train is empty or not available
        if self.X_train is None or self.X_train.empty:
            # If X_train is not available, set y_pred to 50 for all entries in X_test
            self.create_x_test()
            self.y_pred = [50] * len(self.X_test)
        else:
            # Train and predict using RandomForestRegressor
            model = RandomForestRegressor()
            try:
                model.fit(self.X_train, self.y_train)
                self.create_x_test()
                self.y_pred = model.predict(self.X_test)
            except NotFittedError:
                self.y_pred = [50] * len(self.X_test)

        return self.y_pred

    
    def predicted_data(self):
        # Concatenate predictions with X_test
        self.X_test['accuracy'] = self.y_pred
        
        # Ensure that the values are capped at 100
        self.X_test['accuracy'] = self.X_test['accuracy'].apply(lambda x: min(x, 100))
        
        return self.X_test

# Initialize and run prediction
# app = create_app()
# with app.app_context():
#     predict_type = "0"
    
#     subject = "L"
#     predict = PredictThreshold(predict_type, subject, 5)
#     prep = PrepThreshold(subject)
#     print(prep.load_and_save())
    # print(predict.predicted_data())