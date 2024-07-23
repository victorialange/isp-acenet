# this is a python script to analyze the dataset in parallel and generate plots
# planned to be used inside a job script on Siku
# uses model from sklearn and data visualization tools

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from dask.distributed import Client
import joblib

def replace_valid_skip_with_nan(df, columns):
    for column in columns:
        df[column] = df[column].replace('Valid skip', np.nan)
    return df

def range_to_midpoint(value, mapping):
    if value in mapping:
        return mapping[value]
    return value

def add_percentage(ax):
    """
    Function to add percentages on the bars in a bar plot.
    """
    for p in ax.patches:
        width = p.get_width()
        height = p.get_height()
        x, y = p.get_xy()
        if height > 0:
            total = sum([p.get_height() for p in ax.patches if p.get_x() == x])
            percentage = f'{height / total * 100:.1f}%'
            # Adjust the vertical position based on the height of the bar
            offset = height * 0.3 if height < 15 else height * 0
            ax.annotate(percentage, (x + width / 2, y + height + offset), ha='center', va='bottom', fontsize=10, color='black', rotation=22.5, bbox=dict(boxstyle="round,pad=0.3", edgecolor="none", facecolor="white", alpha=0.5))

def add_values(ax):
    """
    Function to add values on the bars in a bar plot.
    """
    for p in ax.patches:
        width = p.get_width()
        height = p.get_height()
        x, y = p.get_xy()
        if height > 0:
            value = f'{height:.0f}'
            ax.annotate(value, (x + width / 2, y + height), ha='center', va='bottom', fontsize=10, color='black', rotation=45, bbox=dict(boxstyle="round,pad=0.3", edgecolor="none", facecolor="white", alpha=0.5))

def aggregate_employment_status(row):
    """
    Function to aggregate employment status into broader categories.
    """
    respondent_status = row['Employed_Status_Respondent']
    spouse_status = row['Employed_Status_Spouse']

    if respondent_status == 'Employed' and spouse_status == 'Employed':
        return 'Both Employed'
    elif respondent_status == 'Employed' or spouse_status == 'Employed':
        return 'One Employed'
    else:
        return 'None Employed'

def aggregate_work_schedule(row):
    """
    Function to aggregate work schedules into broader categories.
    """
    respondent_schedule = row['Work_Schedule_Type_Respondent']
    spouse_schedule = row['Work_Schedule_Type_Spouse']
    
    regular = [
        "A regular daytime schedule or shift",
        "A regular evening shift",
        "A regular night shift"
    ]
    irregular = [
        "A rotating shift",
        "A split shift",
        "On call only",
        "On call in addition to scheduled hours",
        "An irregular schedule"
    ]
    if respondent_schedule in regular and spouse_schedule in regular:
        return 'Both Regular Schedule'
    elif respondent_schedule in irregular and spouse_schedule in irregular:
        return 'Both Irregular Schedule'
    elif (respondent_schedule in regular and spouse_schedule in irregular) or (respondent_schedule in irregular and spouse_schedule in regular):
        return 'One Regular, One Irregular Schedule'
    elif (respondent_schedule in regular and spouse_schedule in ['Other', 'Valid Skip']) or (respondent_schedule in ['Other', 'Valid Skip'] and spouse_schedule in regular):
        return 'One Regular, One Other/Valid Skip'
    elif (respondent_schedule in irregular and spouse_schedule in ['Other', 'Valid Skip']) or (respondent_schedule in ['Other', 'Valid Skip'] and spouse_schedule in irregular):
        return 'One Irregular, One Other/Valid Skip'
    else:
        return 'Other'
            
# prevent issue related to the multiprocessing module in Python by moving main logic to main function & using  if __name__ == '__main__': safeguard at the end
def main():
    # Load cleaned data
    file_path = 'data/survey_2023_cleaned_data.csv'
    df = pd.read_csv(file_path)

    # Initialize Dask client for parallel processing
    client = Client()

    # Replace "Valid skip" with NaN in numeric columns
    numeric_columns = [
        'Annual_Cost_Daycare', 'Annual_Cost_Relative_Care', 'Annual_Cost_Family_Care',
        'Annual_Cost_Before_After_School', 'Annual_Cost_Other_Care', 'Annual_Cost_Care_Total',
        'Total_Household_Income_Grouped'
    ]
    df = replace_valid_skip_with_nan(df, numeric_columns)

    # Handle infinite values explicitly
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Midpoint dictionaries
    cost_midpoint_dict = {
        '$0 per year': 0,
        '$1 to $2,999 per year': 1500,
        '$3,000 to $7,999 per year': 5500,
        '$8,000 or more per year': 10000
    }
    total_income_midpoint_dict = {
        'Under $20,000': 10000,
        '$20,000 to $39,999': 30000,
        '$40,000 to $59,999': 50000,
        '$60,000 to $79,999': 70000,
        '$80,000 to $99,999': 90000,
        '$100,000 to $149,999': 125000,
        '$150,000 and over': 175000
    }

    # Apply the midpoint conversion
    df['Annual_Cost_Daycare'] = df['Annual_Cost_Daycare'].apply(range_to_midpoint, args=(cost_midpoint_dict,))
    df['Annual_Cost_Relative_Care'] = df['Annual_Cost_Relative_Care'].apply(range_to_midpoint, args=(cost_midpoint_dict,))
    df['Annual_Cost_Family_Care'] = df['Annual_Cost_Family_Care'].apply(range_to_midpoint, args=(cost_midpoint_dict,))
    df['Annual_Cost_Before_After_School'] = df['Annual_Cost_Before_After_School'].apply(range_to_midpoint, args=(cost_midpoint_dict,))
    df['Annual_Cost_Other_Care'] = df['Annual_Cost_Other_Care'].apply(range_to_midpoint, args=(cost_midpoint_dict,))
    df['Annual_Cost_Care_Total'] = df['Annual_Cost_Care_Total'].apply(range_to_midpoint, args=(cost_midpoint_dict,))
    df['Total_Household_Income_Grouped'] = df['Total_Household_Income_Grouped'].apply(range_to_midpoint, args=(total_income_midpoint_dict,))

    # print base statistics for numerical columns
    print(df[numeric_columns].describe(include='all'))

    # Filter out provinces with zero respondents to avoid plotting inconsistencies
    province_count = df['Province'].value_counts()
    print("Province value counts:")
    print(df['Province'].value_counts())

    # Ensure all provinces are included in the plots
    provinces = df['Province'].unique()
    
    # Exploratory Data Analysis (EDA)
    # Increase figure size for better readability
    # Plotting the critical analysis
    # Remove rows with NaN values in critical numerical columns
    df_cleaned = df.dropna(subset=['Annual_Cost_Care_Total', 'Total_Household_Income_Grouped'])

    # Create subplots
    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(20, 25))

    # Aggregate employment status & work schedule type for simpler chart
    df['Combined_Employment_Status'] = df.apply(aggregate_employment_status, axis=1)
    df_cleaned['Combined_Work_Schedule_Type'] = df.apply(aggregate_work_schedule, axis=1)

    # Plot 1: Distribution of Total Annual Child Care Costs
    sns.histplot(df_cleaned['Annual_Cost_Care_Total'], bins=20, kde=True, ax=axes[0, 0])
    axes[0, 0].set_title('Distribution of Total Annual Child Care Costs (parents not using child care excluded)')
    axes[0, 0].set_xlabel('Annual Cost of Child Care')
    axes[0, 0].set_ylabel('Frequency')

    # Plot 2: Count of Main Care Arrangements
    df['Main_Care_Arrangement'].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=axes[0, 1])
    axes[0, 1].set_title('Main Care Arrangements')
    axes[0, 1].set_ylabel('')

    # Plot 3: Employment Status and Main Care Arrangement
    df_employment_care = df.groupby(['Combined_Employment_Status', 'Main_Care_Arrangement']).size().unstack().fillna(0)
    df_employment_care.plot(kind='bar', stacked=True, ax=axes[1, 0])
    axes[1, 0].set_title('Employment Status vs. Main Care Arrangement')
    axes[1, 0].set_xlabel('Employment Status')
    axes[1, 0].set_ylabel('Count')
    axes[1, 0].legend(title='Main Care Arrangement')
    axes[1, 0].tick_params(axis='x', rotation=45)
    add_percentage(axes[1, 0])

    # Plot 4: Work Schedule Type and Main Care Arrangement
    df_work_schedule_care = df_cleaned.groupby(['Combined_Work_Schedule_Type', 'Main_Care_Arrangement']).size().unstack().fillna(0)
    df_work_schedule_care.plot(kind='bar', stacked=True, ax=axes[1, 1])
    axes[1, 1].set_title('Work Schedule vs. Main Care Arrangement (parents not using child care excluded)')
    axes[1, 1].set_xlabel('Work Schedule Type')
    axes[1, 1].set_ylabel('Count')
    axes[1, 1].legend(title='Main Care Arrangement')
    axes[1, 1].tick_params(axis='x', rotation=45)
    add_percentage(axes[1, 1])


    # Plot 5: Count of Respondents by Province and Employment Status
    df_grouped_employment = df.groupby(['Province', 'Combined_Employment_Status']).size().unstack().fillna(0)
    df_grouped_employment.plot(kind='bar', stacked=True, ax=axes[2, 0], cmap='viridis', alpha=0.7)
    axes[2, 0].set_title('Respondents and Employment Status by Province')
    axes[2, 0].set_xlabel('Province')
    axes[2, 0].set_ylabel('Count')
    axes[2, 0].legend(title='Employment Status')
    axes[2, 0].tick_params(axis='x', rotation=45)
    add_percentage(axes[2, 0])

    # Plot 6: Comparison of Total Household Income and Annual Cost of Care by Province
    df_grouped = df_cleaned.groupby('Province').agg({
        'Total_Household_Income_Grouped': 'mean',
        'Annual_Cost_Care_Total': 'mean'
    }).reset_index()

    df_grouped.set_index('Province').plot(kind='bar', ax=axes[2, 1], width=0.4)
    axes[2, 1].set_title('Average Income and Annual Cost of Care by Province (parents not using child care excluded)')
    axes[2, 1].set_xlabel('Province')
    axes[2, 1].set_ylabel('Average Income and Cost')
    axes[2, 1].legend(['Avg Income', 'Avg Annual Cost of Care'], loc='upper left')
    axes[2, 1].tick_params(axis='x', rotation=45)
    add_values(axes[2, 1])

    plt.tight_layout()
    plt.savefig('figures/combined_plots.png')
    plt.close()

    # Additional Plots with Correlation Analysis
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(20, 20))

    # Plot 7: Main Care Arrangement and Preferred Type of Main Care
    df_care_preferred_type = df.groupby(['Main_Care_Arrangement', 'Preferred_Type_Main_Child_Care_Arrangement']).size().unstack().fillna(0)
    df_care_preferred_type.plot(kind='bar', stacked=True, ax=axes[0, 0])
    axes[0, 0].set_title('Main Care Arrangement vs. Preferred Type for main care')
    axes[0, 0].set_xlabel('Main Care Arrangement')
    axes[0, 0].set_ylabel('Count')
    axes[0, 0].legend(title='Preferred Type Main Care')
    axes[0, 0].tick_params(axis='x', rotation=45)
    add_percentage(axes[0, 0])

    # Plot 8: Main Reason for Not Using Care and School Attendance
    df_reason_school = df.groupby(['Main_Reason_Not_Using_Care', 'School_Attendance']).size().unstack().fillna(0)
    df_reason_school.plot(kind='bar', stacked=True, ax=axes[0, 1])
    axes[0, 1].set_title('Main Reason for Not Using Care vs. School Attendance')
    axes[0, 1].set_xlabel('Main Reason')
    axes[0, 1].set_ylabel('Count')
    axes[0, 1].legend(title='School Attendance')
    axes[0, 1].tick_params(axis='x', rotation=45)
    add_percentage(axes[0, 1])

    # Correlation Heatmap
    correlation_matrix = df_cleaned[['Annual_Cost_Care_Total', 'Total_Household_Income_Grouped']].corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', ax=axes[1, 0])
    axes[1, 0].set_title('Correlation Heatmap of Annual Care Cost and Total Household Income')

    plt.tight_layout()
    plt.savefig('figures/additional_plots_with_correlation.png')
    plt.close()

    # Model Selection and Training
    # Prepare data for model training
    # Filtered relevant columns for analysis
    critical_columns = [
        'Main_Difficulty_Finding_Care', 'Difficulty_Finding_Care_Arrangement', 'Attended_Child_Care_Three_Months',
        'Employed_Status_Respondent', 'Employed_Status_Spouse', 'Part_Time_Full_Time_Work_Respondent',
        'Part_Time_Full_Time_Work_Spouse', 'Main_Activity_Respondent', 'Main_Activity_Spouse',
        'Satisfaction_Balance_Job_Home_Life', 'Difficulty_Family_Responsibilities_Due_To_Work',
        'Difficulty_Work_Responsibilities_Due_To_Family', 'Work_Schedule_Type_Respondent',
        'Work_Schedule_Type_Spouse', 'Annual_Cost_Daycare', 'Annual_Cost_Relative_Care',
        'Annual_Cost_Family_Care', 'Annual_Cost_Before_After_School', 'Annual_Cost_Other_Care',
        'Annual_Cost_Care_Total', 'Province', 'Total_Household_Income_Grouped', 'Num_Children', 'Spouse_Flag',
        'Immigration_Canada_Five_Years_Household', 'Visible_Minority_Household', 'Indigenous_Group_Household',
        'Born_In_Canada_Household', 'Num_Care_Arrangements', 'Main_Care_Arrangement', 'Main_Care_Reason',
        'Main_Reason_Not_Using_Care', 'Waitlist_Care', 'Ever_Used_Care', 'School_Attendance',
        'Most_Important_Criteria_Decision_Child_Care_Arrangement', 'Preferred_Type_Main_Child_Care_Arrangement',
        'Preferred_Num_Hours_Per_Week_Child_Care', 'Age_Respondent_Grouped', 'Age_Spouse_Grouped',
        'Child_Age_Grouped', 'Subsidy_Flag', 'Industry_Respondent', 'Industry_Spouse', 'Occupation_Respondent',
        'Occupation_Spouse'
    ]
    
    # Filtered relevant columns for analysis
    df_filtered = df[critical_columns]

    # Use aggregated employment status and work schedule type columns
    df_filtered['Combined_Employment_Status'] = df_filtered.apply(aggregate_employment_status, axis=1)
    df_filtered['Combined_Work_Schedule_Type'] = df_filtered.apply(aggregate_work_schedule, axis=1)
    
    X = df_filtered
    y = df_filtered['Main_Care_Arrangement']

    # Convert categorical data to numeric
    X = pd.get_dummies(X, drop_first=True)

    # Handle NaN values
    X = X.fillna(X.mean())

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Train a Random Forest Classifier
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)

    # Predictions
    y_pred = rf_model.predict(X_test)

    # Evaluation
    accuracy = accuracy_score(y_test, y_pred)
    conf_matrix = confusion_matrix(y_test, y_pred)
    class_report = classification_report(y_test, y_pred)

    print("Accuracy:", accuracy)
    print("Confusion Matrix:")
    print(conf_matrix)
    print("Classification Report:")
    print(class_report)

    # Plot confusion matrix
    plt.figure(figsize=(10, 7))
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', xticklabels=rf_model.classes_, yticklabels=rf_model.classes_)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix')
    
    plt.tight_layout()
    plt.savefig('model/confusion_matrix.png')
    plt.close()

    # Feature Importance
    feature_importance = rf_model.feature_importances_
    features = X.columns
    importance_df = pd.DataFrame({'Feature': features, 'Importance': feature_importance}).sort_values(by='Importance', ascending=False)
    print("\nFeature Importance:")
    print(importance_df)

    # Save the model
    joblib.dump(rf_model, 'model/random_forest_model.pkl')
    print("Model saved as 'random_forest_model.pkl'")

if __name__ == '__main__':
    main()
