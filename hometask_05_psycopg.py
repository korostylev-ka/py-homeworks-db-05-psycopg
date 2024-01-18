import csv

import psycopg2
import configparser

class ClientsDB():

    def __init__(self):
        config = configparser.ConfigParser()
        config.read('database.ini')
        database_ = config['Database']['database_name']
        if len(database_) == 0:
            database_input = input('There is no DATABASE in file. Please, enter name of DB here\n')
            self.database = database_input
        else:
            self.database = database_
        user_ = config['Database']['user']
        if len(user_) == 0:
            user_input = input('There is no user in file. Please, enter user here\n')
            self.user = user_input
        else:
            self.user = user_
        password_ = config['Database']['password']
        if len(password_) == 0:
            password_input = input('There is no password in file. Please, enter password of DB here\n')
            self.password = password_input
        else:
            self.password = password_
        self.connect = psycopg2.connect(database=self.database, user=self.user, password=self.password)

    def create_tables(self):
        with self.connect.cursor() as cur:
            cur.execute("""  
                    DROP TABLE phone;  
                    DROP TABLE client;        
                """)
            cur.execute("""
                    CREATE TABLE IF NOT EXISTS client(
                        id SERIAL PRIMARY KEY,
                        first_name VARCHAR(40) NOT NULL,
                        second_name VARCHAR(40) NOT NULL,
                        email VARCHAR(50) NOT NULL UNIQUE
                    );
                """)
            cur.execute("""
                    CREATE TABLE IF NOT EXISTS phone(
                        id SERIAL PRIMARY KEY,
                        client_id INTEGER NOT NULL REFERENCES client(id),
                        phone_number VARCHAR(15) NOT NULL UNIQUE                
                    );
                """)
            self.connect.commit()
        cur.close()

    def add_client(self, first_name: str, second_name: str, email: str) -> int:
        with self.connect.cursor() as cur:
            cur.execute("""
                INSERT INTO client(first_name, second_name, email) VALUES(%s, %s, %s) RETURNING id
             """, (first_name, second_name, email))
            client_id = cur.fetchone()
            self.connect.commit()
        cur.close()
        return client_id

    def add_phone_number(self, id: int, phone_number: str) -> int:
        with self.connect.cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO phone(client_id, phone_number) VALUES(%s, %s) RETURNING id
                 """, (id, phone_number))
                id = cur.fetchone()
                self.connect.commit()
                return id
            except:
                print('Check cliend ID is correct!')
        cur.close()

    def delete_phone_number(self, phone_number: str):
        with self.connect.cursor() as cur:
            # get client id
            try:
                cur.execute("""
                    SELECT client_id FROM phone WHERE (phone_number = %s);
                    """, (phone_number,))
                client_id = cur.fetchone()[0]
                cur.execute("""
                    DELETE FROM phone WHERE phone_number = %s;
                    """, (phone_number,))

            except:
                print(f'There is no phone number {phone_number} in base!')
                return
        cur.close()

    def __get_phone_list_by_client_id__(self, id: int):
        with self.connect.cursor() as cur:
            user_phones = []
            cur.execute("""
                SELECT phone_number FROM phone WHERE (client_id = %s);
                """, (id,))
            phones = cur.fetchall()
            for phone in phones:
                user_phones.append(phone[0])
            return user_phones
        cur.close()

    def __get_client_by_id__(self, id: int):
        with self.connect.cursor() as cur:
            try:
                cur.execute("""
                    SELECT first_name, second_name, email FROM client WHERE (id = %s);
                    """, (id,))
                client = cur.fetchone()
                client_dict = {'First name:': '', 'Second name:': '', 'Email:': '', 'Phone:': []}
                client_dict['First name:'] = client[0]
                client_dict['Second name:'] = client[1]
                client_dict['Email:'] = client[2]
                client_dict['Phone:'] = self.__get_phone_list_by_client_id__(id)
                return client_dict
            except:
                print(f'There is no client with id {id}')
        cur.close()

    def get_client_by_field(self):
        field = 0
        field_choose = 0
        field_name = ""
        while True:
            field = input('Please input column name you want to find:\n1 - First name\n2 - Second name\n3 - Email\n')
            if (field == '1') or (field == '2') or (field == '3'):
                field_choose = int(field)
                break
            else:
                print('Error. Try more time')
        if field_choose == 1:
            field_name = "first_name"
        elif field_choose == 2:
            field_name = "second_name"
        elif field_choose == 3:
            field_name = "email"
        field_value = input(f"Please enter value of {field_name}\n")
        with self.connect.cursor() as cur:
            clients_list = []
            client_info_list = []
            client_phone_list = []
            # get client id(maybe several id's, if clients hava same name and second name)
            cur.execute(f"""
                        SELECT id FROM client WHERE {field_name} = %s;
                        """, (field_value,))
            id_list = cur.fetchall()
            # get client info
            cur.execute(f"""
                        SELECT first_name, second_name, email FROM client WHERE {field_name} = %s;
                        """, (field_value,))
            # client_info_list = cur.fetchall()
            clients = cur.fetchall()
            print(clients)
            for client in clients:
                client_dict = {'First name:': '', 'Second name:': '', 'Email:': '', 'Phone:': []}
                client_dict['First name:'] = client[0]
                client_dict['Second name:'] = client[1]
                client_dict['Email:'] = client[2]
                clients_list.append(client_dict)
                client_info_list.append(list(client))
            # get client phones if exist
            for index, value in enumerate(id_list):
                user_phones = []
                cur.execute("""
                            SELECT phone_number FROM phone WHERE (client_id = %s);
                            """, value)
                phones = cur.fetchall()
                for phone in phones:
                    user_phones.append(phone[0])
                # If client doesn't has phone number
                if len(user_phones) == 0:
                    user_phones.append('NO PHONE NUMBER')
                client_phone_list.append(user_phones)
                clients_list[index]['Phone:'] = user_phones
            print(clients_list)
            fieldnames = ["First name", "Second name", "Email", "Phones"]
            with open(f'get_by_field_{field_name}_{field_value}.csv', 'w') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(fieldnames)
                for client in clients_list:
                    writer.writerow(client.values())
        cur.close()

    def get_client_by_name(self, first_name: str):
        with self.connect.cursor() as cur:
            clients_list = []
            client_info_list = []
            client_phone_list = []
            # get client id(maybe several id's, if clients hava same name and second name)
            cur.execute("""
                        SELECT id FROM client WHERE (first_name = %s);
                        """, (first_name,))
            id_list = cur.fetchall()
            # get client info
            cur.execute("""
                        SELECT first_name, second_name, email FROM client WHERE (first_name = %s);
                        """, (first_name,))
            # client_info_list = cursor.fetchall()
            clients = cur.fetchall()
            for client in clients:
                client_dict = {'First name:': '', 'Second name:': '', 'Email:': '', 'Phone:': []}
                client_dict['First name:'] = client[0]
                client_dict['Second name:'] = client[1]
                client_dict['Email:'] = client[2]
                clients_list.append(client_dict)
                client_info_list.append(list(client))
            # get client phones if exist
            for index, value in enumerate(id_list):
                user_phones = []
                cur.execute("""
                            SELECT phone_number FROM phone WHERE (client_id = %s);
                            """, value)
                phones = cur.fetchall()
                for phone in phones:
                    user_phones.append(phone[0])
                # If client doesn't has phone number
                if len(user_phones) == 0:
                    user_phones.append('NO PHONE NUMBER')
                client_phone_list.append(user_phones)
                clients_list[index]['Phone:'] = user_phones
            print(clients_list)
            fieldnames = ["First name", "Second name", "Email", "Phones"]
            with open(f'get_by_name_{first_name}.csv', 'w') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(fieldnames)
                for client in clients_list:
                    writer.writerow(client.values())
        cur.close()

    def get_client_by_phone(self, phone_number: str):
        with self.connect.cursor() as cur:
            # get client id
            try:
                cur.execute("""
                    SELECT client_id FROM phone WHERE (phone_number = %s);
                    """, (phone_number,))
                client_id = cur.fetchone()[0]
                cur.close()
            except:
                print(f'There is no phone number {phone_number} in base!')
                return
            # get client info
            client_info = self.__get_client_by_id__(client_id)
            with open(f'get_by_phone_{phone_number}.csv', 'w') as f:
                writer = csv.writer(f, delimiter=';')
                # writer.writerow(fieldnames)
                writer.writerow(client_info.values())
            return client_info


    def edit_client(self, id, first_name, second_name, email: int):
        with self.connect.cursor() as cur:
            cur.execute("""
                UPDATE client SET first_name = %s, second_name = %s, email = %s WHERE id = %s RETURNING id;
                """, (first_name, second_name, email, id))
            client_id = cur.fetchone()
            self.connect.commit()
        cur.close()
        return client_id

    def delete_client(self, id: int):
        with self.connect.cursor() as cur:
            cur.execute("""
                DELETE FROM phone WHERE client_id = %s;
                """, (id,))
            cur.execute("""
               DELETE FROM client WHERE id = %s;
                """, (id,))
            self.connect.commit()
        cur.close()

client = ClientsDB()
client.create_tables()
client.add_client("Petya", "Petrov", "mail@mail.ru")
client.add_client("Vasya", "Ivanov", "mail2@mail.ru")
client.add_client("Vasya", "Sidorov", "mail3@mail.ru")
client.add_phone_number(1, "89045400000")
client.add_phone_number(1, "89045400001")
client.add_phone_number(2, "89045400002")
client.delete_phone_number("89045400001")
client.edit_client(1,"Petya2", "Petrov2", "mail",)
client.get_client_by_phone("89045400002")
client.get_client_by_name("Petya")
client.get_client_by_field()



