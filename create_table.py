import sqlite3

# Connect to SQLite database (It will create the file if it doesn't exist)
conn = sqlite3.connect('bank_database.db')
cursor = conn.cursor()

# Enable Foreign Key support
cursor.execute("PRAGMA foreign_keys = ON;")

# 1. Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS Customer (
    CustomerID INTEGER PRIMARY KEY,
    NationalID TEXT NOT NULL UNIQUE,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    BirthDate TEXT,
    PhoneNumber TEXT,
    CreatedAt TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Account (
    AccountID INTEGER PRIMARY KEY,
    CustomerID INTEGER,
    AccountNumber TEXT NOT NULL UNIQUE,
    AccountType TEXT,
    Balance REAL,
    Status TEXT,
    CreatedAt TEXT,
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS "Transaction" (
    TransactionID INTEGER PRIMARY KEY,
    AccountID INTEGER,
    TransactionType TEXT,
    Amount REAL,
    TransactionDate TEXT,
    Description TEXT,
    FOREIGN KEY (AccountID) REFERENCES Account(AccountID)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Transfer (
    TransferID INTEGER PRIMARY KEY,
    FromAccountID INTEGER,
    ToAccountID INTEGER,
    Amount REAL,
    TransferDate TEXT,
    FOREIGN KEY (FromAccountID) REFERENCES Account(AccountID),
    FOREIGN KEY (ToAccountID) REFERENCES Account(AccountID)
);
""")

# 2. Insert Customer Data
customers = [
    (1, '4280387012', 'Ali', 'Rezaei', '1976-10-02', '09127763170', '2022-07-20 12:44:28'),
    (2, '4443818037', 'Sara', 'Ahmadi', '1997-02-11', '09120008063', '2022-12-01 04:14:48'),
    (3, '6296057401', 'Reza', 'Karimi', '1968-03-10', '09121436587', '2020-07-17 11:54:36'),
    (4, '3531559090', 'Neda', 'Mohammadi', '1992-05-22', '09125480293', '2020-03-05 12:21:15'),
    (5, '2143036727', 'Hossein', 'Rashidi', '1980-12-03', '09129671234', '2020-09-10 09:45:00'),
    (6, '5310493680', 'Fatemeh', 'Esfahani', '1975-07-27', '09127613488', '2021-02-14 02:14:14'),
    (7, '6812268282', 'Mohammad', 'Khan', '1977-11-18', '09129068288', '2020-07-02 03:55:23'),
    (8, '7462725203', 'Maryam', 'Hosseini', '1991-06-14', '09125088995', '2022-10-01 07:40:11')
]
cursor.executemany("INSERT OR IGNORE INTO Customer VALUES (?,?,?,?,?,?,?)", customers)

# 3. Insert Account Data
accounts = [
    (1, 1, 'ACC100001', 'Savings', 5000.0, 'Active', '2020-01-16 08:00:00'),
    (2, 1, 'ACC100002', 'Checking', 1500.0, 'Active', '2020-02-10 11:30:00'),
    (3, 2, 'ACC200001', 'Savings', 10000.0, 'Active', '2021-05-05 09:20:00'),
    (4, 3, 'ACC300001', 'Checking', 250.5, 'Active', '2021-06-15 14:45:00'),
    (5, 4, 'ACC400001', 'Savings', 7500.0, 'Active', '2021-07-01 13:10:00'),
    (6, 5, 'ACC500001', 'Checking', 50.75, 'Inactive', '2020-03-08 10:00:00'),
    (7, 6, 'ACC600001', 'Savings', 12500.0, 'Active', '2022-01-20 16:30:00'),
    (8, 7, 'ACC700001', 'Checking', 0.0, 'Active', '2021-09-09 08:25:00'),
    (9, 7, 'ACC700002', 'Savings', 300.0, 'Active', '2022-11-11 09:45:00'),
    (10, 8, 'ACC800001', 'Checking', 980.9, 'Active', '2020-04-14 17:00:00'),
    (11, 2, 'ACC200002', 'Checking', 4300.5, 'Active', '2022-12-25 10:10:00'),
    (12, 3, 'ACC300002', 'Savings', 150.0, 'Inactive', '2021-10-30 12:12:12')
]
cursor.executemany("INSERT OR IGNORE INTO Account VALUES (?,?,?,?,?,?,?)", accounts)

# 4. Insert Transaction Data
transactions = [
    (1, 1, 'Interest', 1785.98, '2022-09-16 12:58:50', 'Interest credit'),
    (2, 1, 'Interest', 641.46, '2022-10-07 16:08:18', 'Interest credit'),
    (3, 1, 'Withdrawal', 380.34, '2022-09-23 19:57:09', 'Check withdrawal'),
    (4, 2, 'Deposit', 1473.17, '2022-08-18 03:22:27', 'Mobile deposit'),
    (5, 2, 'Payment', 309.33, '2023-08-28 16:16:03', 'Utility bill payment'),
    (6, 2, 'Interest', 1841.01, '2020-12-27 12:45:52', 'Interest credit'),
    (7, 3, 'Fee', 10.56, '2022-04-24 10:45:55', 'Service charge'),
    (8, 3, 'Deposit', 422.58, '2021-04-26 04:51:34', 'Mobile deposit'),
    (9, 3, 'Transfer In', 227.87, '2023-02-10 17:18:45', 'Transfer from account 9'),
    (10, 3, 'Deposit', 1117.51, '2021-10-18 18:18:28', 'Mobile deposit'),
    (11, 4, 'Transfer Out', 400.99, '2021-05-06 06:52:11', 'Transfer to account 10'),
    (12, 4, 'Deposit', 1244.91, '2022-08-03 02:43:48', 'Mobile deposit'),
    (13, 5, 'Withdrawal', 462.46, '2023-12-17 08:33:51', 'ATM withdrawal'),
    (14, 5, 'Withdrawal', 426.25, '2023-10-09 14:31:42', 'Check withdrawal'),
    (15, 6, 'Fee', 459.3, '2020-06-20 03:31:37', 'Service charge'),
    (16, 6, 'Fee', 174.28, '2021-01-24 08:07:45', 'Monthly fee'),
    (17, 6, 'Withdrawal', 192.31, '2022-07-27 01:06:50', 'ATM withdrawal'),
    (18, 6, 'Withdrawal', 429.11, '2020-10-21 17:38:43', 'ATM withdrawal'),
    (19, 7, 'Deposit', 292.67, '2020-07-03 11:53:07', 'Salary deposit'),
    (20, 7, 'Deposit', 1230.73, '2021-12-04 15:13:46', 'Salary deposit'),
    (21, 8, 'Fee', 21.16, '2020-05-03 07:04:41', 'Service charge'),
    (22, 8, 'Payment', 181.64, '2020-09-15 01:38:06', 'Utility bill payment'),
    (23, 9, 'Transfer In', 438.74, '2023-10-06 22:43:13', 'Transfer from account 12'),
    (24, 9, 'Interest', 163.2, '2021-06-17 08:07:38', 'Interest credit'),
    (25, 9, 'Transfer In', 1347.93, '2023-10-28 16:58:19', 'Transfer from account 8'),
    (26, 9, 'Fee', 185.0, '2021-09-23 00:29:47', 'Service charge'),
    (27, 10, 'Payment', 372.12, '2022-03-08 15:22:39', 'POS payment'),
    (28, 10, 'Payment', 339.97, '2021-12-10 12:47:26', 'POS payment'),
    (29, 11, 'Deposit', 52.97, '2022-03-08 07:40:28', 'Salary deposit'),
    (30, 11, 'Transfer In', 1435.18, '2023-12-19 13:49:42', 'Transfer from account 1'),
    (31, 11, 'Fee', 32.92, '2020-05-23 05:28:33', 'Service charge'),
    (32, 11, 'Transfer In', 1820.68, '2023-06-10 14:03:51', 'Transfer from account 1'),
    (33, 12, 'Withdrawal', 278.8, '2020-12-05 00:25:43', 'Check withdrawal'),
    (34, 12, 'Transfer In', 666.55, '2020-11-17 19:06:12', 'Transfer from account 1'),
    (35, 12, 'Deposit', 1236.3, '2022-05-23 05:06:30', 'Salary deposit')
]
cursor.executemany('INSERT OR IGNORE INTO "Transaction" VALUES (?,?,?,?,?,?)', transactions)

# 5. Insert Transfer Data
transfers = [
    (1, 9, 3, 227.87, '2023-02-10 17:18:45'),
    (2, 4, 10, 400.99, '2021-05-06 06:52:11'),
    (3, 12, 9, 438.74, '2023-10-06 22:43:13'),
    (4, 8, 9, 1347.93, '2023-10-28 16:58:19'),
    (5, 1, 11, 1435.18, '2023-12-19 13:49:42'),
    (6, 1, 11, 1820.68, '2023-06-10 14:03:51'),
    (7, 1, 12, 666.55, '2020-11-17 19:06:12')
]
cursor.executemany("INSERT OR IGNORE INTO Transfer VALUES (?,?,?,?,?)", transfers)

conn.commit()
conn.close()
print("Database created and data inserted successfully!")
