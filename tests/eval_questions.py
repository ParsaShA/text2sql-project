"""The 10 evaluation questions from the project brief + gold SQL (3 levels)."""

EVAL_SET = [
    # ---- Easy -------------------------------------------------------------------------------
    {"id": 1, "level": "easy", "question": "چه داده‌هایی داری؟", "gold_sql": None,
     "note": "Meta question -> expects status=schema_answer"},
    {"id": 2, "level": "easy",
     "question": "نام و نام خانوادگی تمام مشتریانی که بعد از تاریخ '2021-01-01' ثبت‌نام کرده‌اند را نشان بده.",
     "gold_sql": "SELECT FirstName, LastName FROM Customer WHERE CreatedAt > '2021-01-01';"},
    {"id": 3, "level": "easy",
     "question": "لیست تمام حساب‌های فعال (Active) بانکی به همراه موجودی آن‌ها را بیاور.",
     "gold_sql": "SELECT AccountNumber, AccountType, Balance FROM Account WHERE Status = 'Active';"},
    # ---- Medium -----------------------------------------------------------------------------
    {"id": 4, "level": "medium", "question": "فهرست مشتریانی که حساب آن‌ها غیرفعال است را گزارش کنید.",
     "gold_sql": "SELECT DISTINCT c.FirstName, c.LastName FROM Customer c "
                 "JOIN Account a ON c.CustomerID = a.CustomerID WHERE a.Status = 'Inactive';"},
    {"id": 5, "level": "medium",
     "question": "فهرست مشتریانی که بیشترین مبلغ تراکنش (بزرگ‌ترین تک تراکنش) را دارند گزارش کنید.",
     "gold_sql": "SELECT DISTINCT c.FirstName, c.LastName, t.Amount FROM Customer c "
                 "JOIN Account a ON c.CustomerID = a.CustomerID "
                 "JOIN \"Transaction\" t ON a.AccountID = t.AccountID "
                 "WHERE t.Amount = (SELECT MAX(Amount) FROM \"Transaction\");"},
    {"id": 6, "level": "medium",
     "question": "مجموع مبالغ واریز شده (Deposit) برای حساب با شماره حساب 'ACC200001' چقدر است؟",
     "gold_sql": "SELECT SUM(t.Amount) FROM \"Transaction\" t JOIN Account a ON t.AccountID = a.AccountID "
                 "WHERE a.AccountNumber = 'ACC200001' AND t.TransactionType = 'Deposit';"},
    # ---- Hard -------------------------------------------------------------------------------
    {"id": 7, "level": "hard",
     "question": "فهرست حساب‌هایی که فقط نوع تراکنش آن‌ها برداشت (Withdrawal) می‌باشد را گزارش کنید.",
     "gold_sql": "SELECT a.AccountNumber, a.AccountType FROM Account a "
                 "JOIN \"Transaction\" t ON a.AccountID = t.AccountID GROUP BY a.AccountID, a.AccountNumber "
                 "HAVING SUM(CASE WHEN t.TransactionType != 'Withdrawal' THEN 1 ELSE 0 END) = 0;"},
    {"id": 8, "level": "hard",
     "question": "فهرست مشتریانی را به ترتیب کل حجم مالی تراکنش‌ها (مجموع مبالغ واریز، برداشت، جریمه و...) گزارش کنید.",
     "gold_sql": "SELECT c.FirstName, c.LastName, SUM(t.Amount) AS TotalVolume FROM Customer c "
                 "JOIN Account a ON c.CustomerID = a.CustomerID "
                 "JOIN \"Transaction\" t ON a.AccountID = t.AccountID "
                 "GROUP BY c.CustomerID, c.FirstName, c.LastName ORDER BY TotalVolume DESC;",
     "ordered": True},
    {"id": 9, "level": "hard",
     "question": "لیست مشتریانی را بده که در جدول انتقال وجه (Transfer)، هم به عنوان مبدأ و هم به عنوان مقصد حضور داشته‌اند و مبالغ تراکنش‌های آن‌ها را مشخص کن.",
     "gold_sql": "SELECT c_from.FirstName || ' ' || c_from.LastName AS Sender, a_from.AccountNumber AS SenderAccount, "
                 "c_to.FirstName || ' ' || c_to.LastName AS Receiver, a_to.AccountNumber AS ReceiverAccount, t.Amount "
                 "FROM Transfer t JOIN Account a_from ON t.FromAccountID = a_from.AccountID "
                 "JOIN Customer c_from ON a_from.CustomerID = c_from.CustomerID "
                 "JOIN Account a_to ON t.ToAccountID = a_to.AccountID "
                 "JOIN Customer c_to ON a_to.CustomerID = c_to.CustomerID;"},
    # ---- Reflection demos from the simulator tab -------------------------------------------
    {"id": 10, "level": "reflection",
     "question": "مجموع مبالغ انتقال وجه از حساب مبدأ ACC100001 چقدر است؟",
     "gold_sql": "SELECT SUM(t.Amount) FROM Transfer t JOIN Account a ON t.FromAccountID = a.AccountID "
                 "WHERE a.AccountNumber = 'ACC100001';",
     "note": "Naive SQL compares FromAccountID to a string -> runs fine but returns NULL -> semantic reflection"},
]
