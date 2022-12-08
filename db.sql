CREATE TABLE User_Data (
                username varchar, 
                games int, 
                wins int, 
                guesses int, 
                greens int, 
                yellows int, 
                uniques int, 
                guess_distro varchar, 
                last_win int, 
                last_submit int, 
                curr_streak int, 
                max_streak int, 
                PRIMARY KEY (username)
                ); 
            CREATE TABLE User_Stats (
                username varchar,
                win_rate float,
                avg_guesses float,
                green_rate float,
                yellow_rate float,
                FOREIGN KEY (username) REFERENCES User_Data(username)
                );