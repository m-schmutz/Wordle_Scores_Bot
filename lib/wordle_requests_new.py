from selenium import webdriver
from selenium.webdriver.firefox.service import Service
import time



print('Script Starting...')
a = time.time()
options = webdriver.FirefoxOptions()
options.headless = True
options.page_load_strategy = 'eager'
driverService = Service(log_path='./lib/geckodriver.log')
driver = webdriver.Firefox(options=options, service=driverService)
b = time.time()
print(f'[{b-a:0.9f}] Overhead')

start = time.time()
driver.get('https://www.nytimes.com/games/wordle/index.html')
p1 = time.time()
nyt_wordle_state:str = driver.execute_script('return window.localStorage.getItem("nyt-wordle-state")')
p2 = time.time()
wotd = nyt_wordle_state.split('"solution":"')[1][:5] # about twice as fast as json.loads()
p3 = time.time()
driver.quit()

print(f'[{p1-start:0.9f}] driver.get(\'https://www.nytimes.com/games/wordle/index.html\')\n'
    + f'[{p2-p1:0.9f}] driver.execute_script(\'return window.localStorage.getItem("nyt-wordle-state")\')\n'
    + f'[{p3-p2:0.9f}] wotd = nyt_wordle_state.split(\'"solution":"\')[1][:5]\n'
    + f'[{p3-a:0.9f}] TOTAL TIME ELAPSED\nwotd = {wotd}')




# overhead_times = []
# times = []
# for i in range(10):
#     overhead_start = time.time()
#     options = webdriver.FirefoxOptions()
#     options.headless = True
#     options.page_load_strategy = 'eager'
#     driverService = Service(log_path='./lib/geckodriver.log')
#     driver = webdriver.Firefox(options=options, service=driverService)
#     overhead_end = time.time()

#     start = time.time()
#     driver.get('https://www.nytimes.com/games/wordle/index.html')
#     p1 = time.time()
#     nyt_wordle_state:str = driver.execute_script('return window.localStorage.getItem("nyt-wordle-state")')
#     p2 = time.time()
#     wotd = nyt_wordle_state.split('"solution":"')[1][:5]
#     p3 = time.time()
#     driver.quit()

#     overhead_times.append(overhead_end - overhead_start)
#     times.append(p3 - start)

# avg_overhead_time = sum(overhead_times) / 10
# avg_time = sum(times) / 10
# print(f'Average overhead time: {avg_overhead_time} seconds\nAverage execution time: {avg_time} seconds')