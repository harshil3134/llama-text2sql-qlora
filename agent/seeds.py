"""
Unified Enterprise Database: Multi-table schema with rich, realistic relational data.
Includes departments, employees, customers, and orders.
"""

UNIFIED_DDL = """CREATE TABLE departments (
  id INT PRIMARY KEY,
  name VARCHAR,
  budget INT,
  location VARCHAR
);

CREATE TABLE employees (
  id INT PRIMARY KEY,
  name VARCHAR,
  department VARCHAR,
  department_id INT,
  role VARCHAR,
  salary INT,
  hire_date DATE
);

CREATE TABLE customers (
  id INT PRIMARY KEY,
  name VARCHAR,
  email VARCHAR,
  city VARCHAR
);

CREATE TABLE orders (
  id INT PRIMARY KEY,
  customer_id INT,
  order_date DATE,
  total_amount DECIMAL(10, 2),
  status VARCHAR
);"""

UNIFIED_SEED_SQL = """
INSERT OR IGNORE INTO departments (id, name, budget, location) VALUES
(1, 'Engineering', 1500000, 'San Francisco'),
(2, 'Sales', 800000, 'New York'),
(3, 'Marketing', 500000, 'Chicago'),
(4, 'HR', 300000, 'Austin');

INSERT OR IGNORE INTO employees (id, name, department, department_id, role, salary, hire_date) VALUES
(1, 'Sarah Chen', 'Engineering', 1, 'Staff Engineer', 145000, '2021-03-15'),
(2, 'Alex Rivera', 'Sales', 2, 'Account Executive', 85000, '2022-06-01'),
(3, 'Marcus Vance', 'Engineering', 1, 'DevOps Engineer', 120000, '2021-11-20'),
(4, 'Elena Rostova', 'Marketing', 3, 'Marketing Lead', 92000, '2023-01-10'),
(5, 'David Kim', 'Sales', 2, 'Account Executive', 78000, '2023-04-12'),
(6, 'Priya Patel', 'Engineering', 1, 'Senior Backend Engineer', 135000, '2022-02-18'),
(7, 'Liam O''Connor', 'HR', 4, 'HR Specialist', 68000, '2023-08-05'),
(8, 'Jessica Alba', 'Sales', 2, 'Sales Director', 115000, '2020-09-14'),
(9, 'Carlos Mendez', 'Engineering', 1, 'Frontend Engineer', 98000, '2023-05-22'),
(10, 'Amina Yusuf', 'Engineering', 1, 'QA Lead', 95000, '2022-10-30');

INSERT OR IGNORE INTO customers (id, name, email, city) VALUES
(1, 'Alice Johnson', 'alice@gmail.com', 'New York'),
(2, 'Bob Smith', 'bob@yahoo.com', 'San Francisco'),
(3, 'Charlie Brown', 'charlie@outlook.com', 'Chicago'),
(4, 'Diana Prince', 'diana@amazon.com', 'Seattle'),
(5, 'Ethan Hunt', 'ethan@imf.org', 'Austin');

INSERT OR IGNORE INTO orders (id, customer_id, order_date, total_amount, status) VALUES
(101, 1, '2024-01-15', 250.00, 'delivered'),
(102, 1, '2024-02-10', 89.50, 'delivered'),
(103, 2, '2024-02-14', 1200.00, 'shipped'),
(104, 3, '2024-02-20', 45.00, 'cancelled'),
(105, 4, '2024-03-01', 540.25, 'delivered'),
(106, 5, '2024-03-05', 820.00, 'pending'),
(107, 2, '2024-03-12', 310.00, 'delivered'),
(108, 4, '2024-03-15', 150.00, 'delivered');
"""

SUGGESTED_QUERIES = [
    "Find employees who are Account Executives with a salary under 90000",
    "Who is the highest paid employee and what is their role?",
    "Show the average salary and employee count for each department",
    "List all customers who live in San Francisco or Seattle",
    "Find the total amount spent by customer Alice Johnson",
    "List employee names along with their department location and budget",
    "Find all orders with a total amount greater than 500 dollars"
]
