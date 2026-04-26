-- MySQL dump 10.13  Distrib 9.4.0, for Win64 (x86_64)
-- Complete netbanking database schema with actual data
-- Database: netbankinglogging

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- Create database if not exists
DROP DATABASE IF EXISTS netbankinglogging;
CREATE DATABASE netbankinglogging CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE netbankinglogging;

-- Users Table
CREATE TABLE users (
  user_id INT NOT NULL,
  username VARCHAR(50) NOT NULL UNIQUE,
  first_name VARCHAR(50) DEFAULT NULL,
  last_name VARCHAR(50) DEFAULT NULL,
  password_hash VARCHAR(255) NOT NULL,
  email VARCHAR(100) DEFAULT NULL,
  phone_number VARCHAR(15) DEFAULT NULL,
  is_active TINYINT(1) DEFAULT 1,
  PRIMARY KEY (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Bank Accounts Table
CREATE TABLE bank_accounts (
  account_number INT NOT NULL,
  user_id INT DEFAULT NULL,
  account_type VARCHAR(20) DEFAULT NULL,
  balance DECIMAL(15,2) DEFAULT 0.00,
  status VARCHAR(20) DEFAULT 'Active',
  PRIMARY KEY (account_number),
  KEY user_id (user_id),
  CONSTRAINT bank_accounts_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id),
  CONSTRAINT bank_accounts_chk_1 CHECK (account_type IN ('Savings','Current'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Bank Details Table
CREATE TABLE bank_details (
  account_number INT NOT NULL,
  bank_name VARCHAR(50) NOT NULL,
  ifsc_code VARCHAR(20) NOT NULL,
  PRIMARY KEY (account_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Login Sessions Table
CREATE TABLE login_sessions (
  session_id INT NOT NULL,
  user_id INT DEFAULT NULL,
  login_time TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  logout_time TIMESTAMP NULL DEFAULT NULL,
  ip_address VARCHAR(45) DEFAULT NULL,
  session_token VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (session_id),
  KEY user_id (user_id),
  CONSTRAINT login_sessions_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Activity Logs Table
CREATE TABLE activity_logs (
  log_id INT NOT NULL,
  session_id INT DEFAULT NULL,
  action_type VARCHAR(50) DEFAULT NULL,
  target_entity VARCHAR(100) DEFAULT NULL,
  reference_id VARCHAR(50) DEFAULT NULL,
  timestamp TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (log_id),
  KEY session_id (session_id),
  CONSTRAINT activity_logs_ibfk_1 FOREIGN KEY (session_id) REFERENCES login_sessions (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Transactions Table
CREATE TABLE transactions (
  transaction_id INT NOT NULL,
  source_account INT DEFAULT NULL,
  dest_account INT DEFAULT NULL,
  amount DECIMAL(15,2) DEFAULT NULL,
  transaction_type VARCHAR(20) DEFAULT NULL,
  otp_code VARCHAR(10) DEFAULT NULL,
  timestamp TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (transaction_id),
  KEY source_account (source_account),
  KEY dest_account (dest_account),
  CONSTRAINT transactions_ibfk_1 FOREIGN KEY (source_account) REFERENCES bank_accounts (account_number),
  CONSTRAINT transactions_ibfk_2 FOREIGN KEY (dest_account) REFERENCES bank_accounts (account_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Beneficiaries Table
CREATE TABLE beneficiaries (
  beneficiary_id INT NOT NULL,
  user_id INT DEFAULT NULL,
  account_number INT DEFAULT NULL,
  nickname VARCHAR(50) DEFAULT NULL,
  relationship_tag VARCHAR(30) DEFAULT NULL,
  PRIMARY KEY (beneficiary_id),
  KEY user_id (user_id),
  CONSTRAINT beneficiaries_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Failed Login Attempts Table
CREATE TABLE failed_login_attempts (
  attempt_id INT NOT NULL,
  user_id INT DEFAULT NULL,
  ip_address VARCHAR(45) DEFAULT NULL,
  attempt_time TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  failure_reason VARCHAR(100) DEFAULT NULL,
  PRIMARY KEY (attempt_id),
  KEY user_id (user_id),
  CONSTRAINT failed_login_attempts_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Device Registry Table
CREATE TABLE device_registry (
  device_fingerprint VARCHAR(100) NOT NULL,
  device_type VARCHAR(50) NOT NULL,
  PRIMARY KEY (device_fingerprint)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Trusted Devices Table
CREATE TABLE trusted_devices (
  device_id INT NOT NULL,
  user_id INT DEFAULT NULL,
  device_fingerprint VARCHAR(100) DEFAULT NULL,
  last_used_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (device_id),
  KEY user_id (user_id),
  CONSTRAINT trusted_devices_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- OTP Validation Table
CREATE TABLE otp_validation (
  otp_code VARCHAR(10) NOT NULL,
  otp_status VARCHAR(20) DEFAULT NULL,
  PRIMARY KEY (otp_code),
  CONSTRAINT otp_validation_chk_1 CHECK (otp_status IN ('Verified','Expired','Failed'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Security Question Bank Table
CREATE TABLE security_question_bank (
  question_id INT NOT NULL,
  question_text VARCHAR(255) DEFAULT NULL,
  difficulty_level VARCHAR(20) DEFAULT NULL,
  PRIMARY KEY (question_id),
  UNIQUE KEY question_text (question_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- User Security Questions Table
CREATE TABLE user_security_questions (
  security_id INT NOT NULL,
  user_id INT DEFAULT NULL,
  answer_hash VARCHAR(255) DEFAULT NULL,
  question_id INT DEFAULT NULL,
  PRIMARY KEY (security_id),
  KEY user_id (user_id),
  KEY question_id (question_id),
  CONSTRAINT user_security_questions_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id),
  CONSTRAINT user_security_questions_ibfk_2 FOREIGN KEY (question_id) REFERENCES security_question_bank (question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Alert Severity Master Table
CREATE TABLE alert_severity_master (
  severity_level VARCHAR(20) NOT NULL,
  default_message_template TEXT,
  PRIMARY KEY (severity_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Fraud Alerts Table
CREATE TABLE fraud_alerts (
  alert_id INT NOT NULL AUTO_INCREMENT,
  user_id INT DEFAULT NULL,
  transaction_id INT DEFAULT NULL,
  severity_level VARCHAR(20) DEFAULT NULL,
  is_resolved TINYINT(1) DEFAULT 0,
  PRIMARY KEY (alert_id),
  KEY user_id (user_id),
  KEY transaction_id (transaction_id),
  CONSTRAINT fraud_alerts_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id),
  CONSTRAINT fraud_alerts_ibfk_2 FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id),
  CONSTRAINT fraud_alerts_chk_1 CHECK (severity_level IN ('Low','Medium','Critical'))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ====================================
-- INSERT DATA
-- ====================================

-- Users data (5 test users)
INSERT INTO users VALUES 
(1,'vikram_s','Vikram','Singh','hash_vik_new_999','vikram.s@gmail.com','9876500001',1),
(2,'priya_p','Priya','Patel','hash_pri_456','priya.patel@yahoo.in','9123400002',1),
(3,'rahul_g','Rahul','Gupta','hash_rah_789','rahul.g_biz@outlook.com','9988700003',1),
(4,'amit_verma','Amit','Verma','hash_ami_321','amit.v@gmail.com','9000100004',0),
(5,'sneha_r','Sneha','Reddy','hash_sne_654','sneha.reddy@techmail.in','8877600005',1);

-- Bank accounts data (5 accounts)
INSERT INTO bank_accounts VALUES 
(1001,1,'Savings',45550.51,'Active'),
(1002,2,'Savings',126250.00,'Active'),
(1003,3,'Current',500000.00,'Active'),
(1004,4,'Savings',1515.00,'Frozen'),
(1005,5,'Savings',8585.76,'Active');

-- Bank details data
INSERT INTO bank_details VALUES 
(1001,'HDFC Bank','HDFC0001234'),
(1002,'HDFC Bank','HDFC0001234'),
(1003,'ICICI Bank','ICIC0007890'),
(5566,'SBI','SBIN0004567'),
(9988,'Axis Bank','UTIB0001122');

-- Login sessions data
INSERT INTO login_sessions VALUES 
(101,1,'2024-02-12 03:30:00','2024-02-12 03:45:00','192.168.1.101','tok_vik_01'),
(102,2,'2024-02-12 05:00:00','2024-02-12 05:15:00','110.22.33.44','tok_pri_02'),
(103,3,'2024-02-12 05:30:00',NULL,'14.139.1.55','tok_rah_03'),
(104,1,'2024-02-12 08:30:00','2024-02-12 08:35:00','192.168.1.101','tok_vik_04'),
(105,5,'2024-02-12 14:40:00','2024-02-12 15:00:00','49.37.12.88','tok_sne_05');

-- Activity logs data
INSERT INTO activity_logs VALUES 
(1,101,'View Balance',NULL,NULL,'2024-02-12 03:35:00'),
(2,101,'Add Beneficiary','Landlord','5566','2024-02-12 03:40:00'),
(3,102,'Fund Transfer','Rahul','5000','2024-02-12 05:10:00'),
(4,103,'Change Password',NULL,NULL,'2024-02-12 05:45:00'),
(5,105,'View Statement',NULL,NULL,'2024-02-12 14:45:00');

-- Transactions data (5 transactions)
INSERT INTO transactions VALUES 
(9001,1001,1002,2000.00,'UPI','567890','2024-02-12 03:42:00'),
(9002,1002,1003,50000.00,'IMPS','123456','2024-02-12 05:10:00'),
(9003,1001,1005,500.00,'UPI','112233','2024-02-12 08:32:00'),
(9004,1003,1001,1000000.00,'NEFT','998877','2024-02-12 09:30:00'),
(9005,1005,1001,100.00,'UPI','445566','2024-02-12 14:50:00');

-- Beneficiaries data
INSERT INTO beneficiaries VALUES 
(1,1,1002,'Priya','Sister'),
(2,1,5566,'Landlord',NULL),
(3,2,1003,'Rahul Consultant',NULL),
(4,3,9988,'Supplier A',NULL),
(5,5,1001,'Dad',NULL);

-- Failed login attempts data
INSERT INTO failed_login_attempts VALUES 
(1,1,'103.45.67.89','2024-02-12 03:25:00','Wrong Password'),
(2,1,'103.45.67.89','2024-02-12 03:26:00','Wrong Password'),
(3,1,'103.45.67.89','2024-02-12 03:27:00','Account Locked'),
(4,4,'192.168.0.50','2024-02-11 04:30:00','User Inactive'),
(5,2,'110.22.33.44','2024-02-12 04:59:00','OTP Timeout');

-- Device registry data
INSERT INTO device_registry VALUES 
('MAC-ADDR-11:22:33','Windows Laptop'),
('MAC-ADDR-44:55:66','iPad Pro'),
('MAC-ADDR-77:88:99','OnePlus 11'),
('MAC-ADDR-AA:BB:CC','Android Phone'),
('MAC-ADDR-DD:EE:FF','iPhone 14');

-- Trusted devices data
INSERT INTO trusted_devices VALUES 
(1,1,'MAC-ADDR-AA:BB:CC','2024-02-10 04:00:00'),
(2,1,'MAC-ADDR-11:22:33','2024-02-11 08:45:00'),
(3,2,'MAC-ADDR-DD:EE:FF','2024-02-12 03:15:00'),
(4,3,'MAC-ADDR-44:55:66','2024-02-12 12:50:00'),
(5,5,'MAC-ADDR-77:88:99','2024-02-12 14:30:00');

-- OTP validation data
INSERT INTO otp_validation VALUES 
('112233','Expired'),
('123456','Verified'),
('445566','Verified'),
('567890','Verified'),
('998877','Verified');

-- Security question bank data
INSERT INTO security_question_bank VALUES 
(1,'What is the name of your first school?','Medium'),
(2,'What city were you born in?','Low'),
(3,'What was your childhood nickname?','Medium'),
(4,'What is your mother\'s maiden name?','High'),
(5,'What is your favorite food?','Low');

-- User security questions data
INSERT INTO user_security_questions VALUES 
(1,1,'hash_dps_delhi',NULL),
(2,2,'hash_mumbai',NULL),
(3,3,'hash_chintu',NULL),
(4,4,'hash_sharma',NULL),
(5,5,'hash_biryani',NULL);

-- Alert severity master data
INSERT INTO alert_severity_master VALUES 
('Critical','Immediate action required: High value risk.');

-- Fraud alerts data
INSERT INTO fraud_alerts VALUES 
(1,1,NULL,'Medium',1),
(2,3,9004,'Critical',0),
(3,4,NULL,'Low',1),
(4,1,9003,'Low',1),
(5,2,9002,'Medium',0),
(7,NULL,9005,'Low',0);

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
