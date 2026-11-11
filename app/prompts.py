"""Prompt templates (LangChain ChatPromptTemplate)."""
from langchain_core.prompts import ChatPromptTemplate

DOMAIN_NOTES = """\
Domain notes (from the data dictionary):
- Dialect: SQLite. "Transaction" is a reserved word: always write it quoted as "Transaction".
- Customer(CustomerID, NationalID, FirstName, LastName, BirthDate, PhoneNumber, CreatedAt)
- Account(AccountID, CustomerID, AccountNumber, AccountType, Balance, Status, CreatedAt)
    AccountType in ('Savings','Checking'); Status in ('Active','Inactive').
    AccountNumber (e.g. 'ACC100001') is TEXT; AccountID is the INTEGER primary key.
- "Transaction"(TransactionID, AccountID, TransactionType, Amount, TransactionDate, Description)
    TransactionType in ('Deposit','Withdrawal','Interest','Fee','Payment','Transfer In','Transfer Out').
- Transfer(TransferID, FromAccountID, ToAccountID, Amount, TransferDate)
    FromAccountID / ToAccountID are INTEGER foreign keys to Account.AccountID, NOT account-number strings.
    To filter by an account number like 'ACC100001' you must JOIN Account.
- Dates are TEXT 'YYYY-MM-DD HH:MM:SS'; compare them as strings.
- Words such as "blocked", "disabled", "closed" mean Account.Status = 'Inactive'.
- Never invent tables or columns. Only SELECT statements.
"""

# Curly braces in DOMAIN_NOTES: none, so it is safe to concatenate into templates.

GENERATE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior data analyst who writes correct SQLite queries for a retail bank database.\n\n"
     "DATABASE SCHEMA:\n{schema}\n\n" + DOMAIN_NOTES + "\n"
     "Decide how to answer the user:\n"
     "- If the user asks a meta question about the data itself (e.g. 'what data do you have?'), set "
     "kind='schema_answer' and write a helpful answer in `answer` (in the user's language) describing "
     "the tables and what they contain. Leave `sql` empty.\n"
     "- Otherwise set kind='sql' and put ONE SQLite SELECT statement in `sql`."),
    ("human", "{question}"),
])

SYNTAX_FIX_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You repair SQLite queries using the exact error message returned by the database engine.\n\n"
     "DATABASE SCHEMA:\n{schema}\n\n" + DOMAIN_NOTES + "\n"
     "Return the corrected query (a single SELECT) in `sql` and a one-sentence `explanation` of what "
     "was wrong. Keep the original intent of the user's question."),
    ("human",
     "User question: {question}\n\n"
     "Failed SQL:\n{sql}\n\n"
     "Database error:\n{error}\n\n"
     "Previous failed attempts (do not repeat them):\n{history}"),
])

# ONE call that both diagnoses a logical problem AND produces the corrected SQL.
SEMANTIC_REFLECT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a meticulous SQL reviewer. The query below executed WITHOUT errors, but that does not "
     "mean it answers the question. Compare the user's question, the SQL, and the actual result.\n\n"
     "DATABASE SCHEMA:\n{schema}\n\n" + DOMAIN_NOTES + "\n"
     "Look for logical problems such as: an unexpected empty/NULL result, a missing JOIN (e.g. comparing "
     "an account-number string to an integer ID), a wrong filter value, a wrong aggregation or column, "
     "duplicated rows caused by a join, or a result that does not match what was asked.\n\n"
     "Rules:\n"
     "- If the result correctly answers the question, set has_issue=false and corrected_sql=null.\n"
     "- If there is a logical problem, set has_issue=true, explain it in `reasoning`, and in the SAME "
     "response provide the fully corrected SELECT in `corrected_sql`. You are the only reviewer; do "
     "not defer to another step.\n"
     "- An empty result can be legitimate (nothing matches). Only flag it if the data/schema suggest "
     "rows should exist."),
    ("human",
     "User question: {question}\n\n"
     "SQL:\n{sql}\n\n"
     "Execution result:\n{result}"),
])
