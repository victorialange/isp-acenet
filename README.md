# ISP Project

## Project Overview

In this Independent Study Project (ISP), an analysis using Python and other libraries like pandas, dask, numpy, matplotlib, seaborn combined with HPC in Siku, will be performed on the Canadian Survey on Early Learning and Child Care in 2023 published by Statistics Canada and will take a deep dive into the trends, correlations with different categories such as parental employment and their work schedules and comparisons across regions Canada-wide.

#### The primary goals of this project are:

- Understanding the current landscape of child care in Canada and identifying patterns, trends, accessibility, costs and challenges **(Trends)**
- Getting a better overview on how these metrics vary across different regions within Canada and identify preferences and potential factors per region such as differences in income and cost **(Regional comparison)**
- Determining how parental employment status and work schedules affect the choice and availability of child care and understand how these depend on each other and assessing reasons for not using child care and alternative arrangements made by families **(Correlation)**

## Description of the dataset

The dataset used for this project is in CSV format made available by Statistics Canada, based on a survey from 2023 on early learning and child care in Canada, which provides the data for the different types of child care arrangements in Canada for that year, including the cost and reasons for that choice, as well as other important information about the parents such as their employment status and their work schedules.

The original dataset contains column names and values that are hard to read, so one has to refer to the codebook in order to identify what these codes (integers) and column names actually represent, as well as to the NAICS 2022 (North American Industry Classification System) and NOC 2021 (National Occupational Classification). For better readability and for referencing the column names mentioned below, please refer to the "survey_2023_cleaned.csv" file found in the same data directory as the original csv file.

The provided data allows us to get an insight on how much has been spent anually on child care by families as well as to identify the most popular type of arrangement chosen, when having a look at the "Annual_Cost_Care_Total" and "Main_Care_Arrangement" columns. The column for the total annual cost of child care is a range of different numbers in CAD as a string, so a midpoint was used in order to proceed with the analysis and get the highest and lowest values (not reflected in the cleaned dataset file, only in the code file where the analysis is performed), meanwhile the column for the main child care arrangement is using string values.

Furthermore, we have the "Total_Household_Income_Grouped", "Employed_Status_Respondent", "Employed_Status_Spouse" (see the "Spouse_Flag" column to determine if that column is applicable in this case) as well as the "Work_Schedule_Type_Respondent" and "Work_Schedule_Type_Spouse" columns that allow us to determine the parental involvement in the labour market, which is important for seeing how that could influence the child care arrangements. The total household income column similar to the annual cost column is using string values that are representing a range of different numbers (midpoint is used for further analysis), meanwhile the columns for the employment status and work schedules are simple strings.

The "Province" column provides insight into what specific region the entries are for - only includes the following 10 provinces:

- Newfoundland and Labrador
- Prince Edward Island
- Nova Scotia
- New Brunswick
- Quebec
- Ontario
- Manitoba
- Saskatchewan
- Alberta
- British Columbia

Note also that missing values are represented by "Not stated" and "Valid skip". The latter however is most likely occurring when a certain column cannot apply to a specific entry due to a value from another column which would contradict that, for example if "Spouse_Flag" is false (i.e. the respondent doesn't have a spouse in the household) then any columns related to spouse cannot have a value by default.
