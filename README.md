# Command Line Interface for an ETrade accounts in python

BY USING THIS SOFTWARE YOU ARE ACCEPTING THE FACT THAT IT WILL HAVE ACCESS TO ALL
YOUR E*TRADE ACCOUNT AND IT CAN AUTOMATICALLY PLACE ORDERS THAT YOU DO OR YOU
DO NOT WANT.<BR>

THIS IS NOT A BUG FREE SOFTWARE AND MANY FUNCTIONALITIES HAVE NOT BEEN TESTED.<BR>
USE THIS SOFTWARE AT YOUR OWN RISK.<BR>

<BR>

GET STARTED
---

- obtain E*Trade sandbox and production keys following the instruction in
  https://developer.etrade.com/ctnt/dev-portal/getArticleByCategory?category=Documentation

- updates keys.txt with the keys

- update the browser_path in settings.txt
   - use browser_path_Windows, browser_path_Linux, browser_path_Darwin accordingly to your operating system
   - this step is necessary for the E*Trade authorization procedure

<BR>


RUN
---

- python run.py sandbox     -> start the platform in the sandbox environment

- python run.py             -> start the platform in the production environment

<BR>


UNSUPPORTED FEATURES
---

- margin accounts are not supported

- multiple legs orders are not supported

- everything that the E*Trade APIs does not support is not supported by this platform
