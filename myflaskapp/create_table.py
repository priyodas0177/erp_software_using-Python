from database import get_connection
conn =get_connection()
cursor=conn.cursor()

# cursor.execute("""
#     CREATE TABLE admin ( 
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     name VARCHAR(50) unique, 
#     password VARCHAR(20), 
#     role VARCHAR(20),
#     is_active BOOLEAN DEFAULT TRUE)""")

# print("table created successfully")




# cursor.execute("""
#     # CREATE TABLE users( 
#     # id INT AUTO_INCREMENT PRIMARY KEY,
#     # fullname VARCHAR(50),
#     # username VARCHAR(50) unique, 
#     # password VARCHAR(20),
#     # email varchar(50),
#     # phone int (15),
#     # gender varchar(10),          
#     # role VARCHAR(20),
#     # is_active BOOLEAN DEFAULT TRUE)""")
    

# print("table created successfully")

#cursor.execute("ALTER TABLE users MODIFY phone VARCHAR(15);")


# cursor.execute("""
#     CREATE TABLE features (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     feature_code VARCHAR(50) UNIQUE,
#     feature_name VARCHAR(100)
# )
# """)


# cursor.execute("""CREATE TABLE user_permissions (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     user_id INT NOT NULL,
#     feature_code VARCHAR(50) NOT NULL,
#     is_allowed TINYINT DEFAULT 1,

#     UNIQUE (user_id, feature_code),
#     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
# )
# """
# )
# print("table created successfully")


# cursor.execute("""
# CREATE TABLE attendance_daily (
#   id BIGINT AUTO_INCREMENT PRIMARY KEY,
#   user_id INT NOT NULL,
#   att_date DATE NOT NULL,

#   in_time DATETIME NULL,
#   out_time DATETIME NULL,
#   stay_minutes INT NULL,

#   status ENUM('absent','present') NOT NULL DEFAULT 'absent',
#   remarks VARCHAR(255) NULL,    
#   details TEXT NULL,            

#   UNIQUE KEY uniq_user_date (user_id, att_date),
#   FOREIGN KEY (user_id) REFERENCES users(id)
# );


# """)
# print("table created successfully")

cursor.execute("""
CREATE TABLE attendance_events (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  event_time DATETIME NOT NULL,
  event_type ENUM('login','logout') NOT NULL,
  ip VARCHAR(45) NULL,
  user_agent VARCHAR(255) NULL,

  INDEX idx_user_time (user_id, event_time),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

""")
print("table created successfully")