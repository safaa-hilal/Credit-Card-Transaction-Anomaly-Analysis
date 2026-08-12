SELECT COUNT(*) FROM customers;
SELECT COUNT (*) FROM transactions;
SELECT * FROM Customers LIMIT 5;
SELECT * FROM transactions LIMIT 5;
PRAGMA table_info(Customers);
PRAGMA table_info(Transactions);

SELECT * FROM Transactions LIMIT 1;
SELECT * FROM Customers LIMIT 1;
SELECT COUNT (*) FROM anomalies;

SELECT * FROM Transactions t
LEFT JOIN anomalies a ON t.TransactionID = a.TransactionID
LIMIT 10;
------------------01 basic questions--------------------------------------------
SELECT SUM(Amount) AS TotalSpent FROM Transactions;       ----1
SELECT AVG(Amount) AS AverageTransaction FROM Transactions; -----2   
SELECT MAX(Amount) AS LargestTransaction FROM Transactions; ------3   

-------------02 cx analysis------ 03 card analysis-----
----------Which income bracket contributes the most total spending?------1
SELECT
    c.IncomeBracket,
    SUM(t.Amount) AS TotalSpending
FROM Customers c
JOIN Transactions t
    ON c.CustomerID = t.CustomerID
GROUP BY c.IncomeBracket
ORDER BY TotalSpending DESC;

-------How much does the average customer spend in each income bracket?-------2

------Which card type generates the most total spending?----3
SELECT
    c.CardType,
    SUM(t.Amount) AS TotalSpending
FROM Customers c
JOIN Transactions t
    ON c.CustomerID = t.CustomerID
GROUP BY c.CardType
ORDER BY TotalSpending DESC;

-----How many customers have each card type?-----4
SELECT
    CardType,
    COUNT(*) AS NumberOfCustomers
FROM Customers
GROUP BY CardType
ORDER BY NumberOfCustomers DESC;

-------geo analysis-----
------Which customer city generates the highest total spending?----1
SELECT
    c.HomeCity,
    SUM(t.Amount) AS TotalSpending
FROM Customers c
JOIN Transactions t
    ON c.CustomerID = t.CustomerID
GROUP BY c.HomeCity
ORDER BY TotalSpending DESC;

UPDATE Customers
SET HomeCity = 'Daqahlia'
WHERE HomeCity = 'DaqahliaDubai';

SELECT
    HomeCity,
    COUNT(*) AS NumberOfCustomers
FROM Customers
GROUP BY HomeCity
ORDER BY HomeCity;
-----How many customers live in each city?-----2
SELECT
    HomeCity,
    COUNT(*) AS NumberOfCustomers
FROM Customers
GROUP BY HomeCity
ORDER BY NumberOfCustomers DESC;
-------individual analysis-------------
-------Who are the Top 10 highest-spending customers?----1
SELECT
    CustomerID,
    SUM(Amount) AS TotalSpending
FROM Transactions
GROUP BY CustomerID
ORDER BY TotalSpending DESC
LIMIT 10;
-------Which customers make the most transactions?----2
SELECT
    CustomerID,
    COUNT(*) AS NumberOfTransactions
FROM Transactions
GROUP BY CustomerID
ORDER BY NumberOfTransactions DESC
LIMIT 10;
-------------04 spending analysis---------
-----How much money was spent in each merchant category?-----1
SELECT
    MerchantCategory,
    SUM(Amount) AS TotalSpending
FROM Transactions
GROUP BY MerchantCategory
ORDER BY TotalSpending DESC;

----How many transactions happened in each merchant category?----2
SELECT MerchantCategory,
       COUNT(*) AS NumberOfTransactions
FROM Transactions
GROUP BY MerchantCategory
ORDER BY NumberOfTransactions DESC;
------Which merchant category has the highest average transaction amount?----3
SELECT
    MerchantCategory,
    AVG(Amount) AS AverageTransaction
FROM Transactions
GROUP BY MerchantCategory
ORDER BY AverageTransaction DESC;
-----"Which income bracket spends the most in each merchant category?"-----4
WITH CategorySpending AS
(
    SELECT
        t.MerchantCategory,
        c.IncomeBracket,
        SUM(t.Amount) AS TotalSpending
    FROM Customers c
    JOIN Transactions t
        ON c.CustomerID = t.CustomerID
    GROUP BY
        t.MerchantCategory,
        c.IncomeBracket
),

RankedCategories AS
(
    SELECT *,
           ROW_NUMBER() OVER
           (
               PARTITION BY MerchantCategory
               ORDER BY TotalSpending DESC
           ) AS rn
    FROM CategorySpending
)

SELECT
    MerchantCategory,
    IncomeBracket,
    TotalSpending
FROM RankedCategories
WHERE rn = 1
ORDER BY MerchantCategory;

-----Which card type spends the most in each merchant category?----5
WITH CategorySpending AS
(
    SELECT
        t.MerchantCategory,
        c.CardType,
        SUM(t.Amount) AS TotalSpending
    FROM Customers c
    JOIN Transactions t
        ON c.CustomerID = t.CustomerID
    GROUP BY
        t.MerchantCategory,
        c.CardType
),

RankedCategories AS
(
    SELECT *,
           ROW_NUMBER() OVER
           (
               PARTITION BY MerchantCategory
               ORDER BY TotalSpending DESC
           ) AS rn
    FROM CategorySpending
)

SELECT
    MerchantCategory,
    CardType,
    TotalSpending
FROM RankedCategories
WHERE rn = 1
ORDER BY MerchantCategory;

-------histogram
SELECT
    CustomerID,
    AVG(Amount) AS AvgTransactionAmount
FROM Transactions
GROUP BY CustomerID;

------scatter plot for trx freq and total spending-----1
SELECT
    CustomerID,
    COUNT(TransactionID) AS TransactionFrequency,
    SUM(Amount) AS TotalSpending
FROM Transactions
GROUP BY CustomerID
ORDER BY TotalSpending DESC;
-------scatter plot for personal deviation-----2
SELECT
    t.TransactionID,
    t.CustomerID,
    t.Date,
    t.Amount,
    t.MerchantCategory,
    t.TransactionCity,

    AVG(t.Amount) OVER (
        PARTITION BY t.CustomerID
    ) AS CustomerAvgTxnAmount

FROM Transactions t
ORDER BY t.CustomerID, t.Date;
------connect to tableau
SELECT
    c.CustomerID,
    c.Age,
    c.HomeCity,
    c.IncomeBracket,
    c.CardType,
    c.AccountOpenDate,
    t.TransactionID,
    t.Date,
    t.Amount,
    t.MerchantCategory,
    t.TransactionCity
FROM Customers c
JOIN Transactions t
    ON c.CustomerID = t.CustomerID;