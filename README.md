# Command line interface for ETrade accounts in python

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

BY USING THIS SOFTWARE YOU ARE ACCEPTING THE FACT THAT IT WILL HAVE ACCESS TO ALL
YOUR ETRADE ACCOUNT DATA AND THAT IT CAN AUTOMATICALLY PLACE ORDERS THAT YOU DO OR YOU
DO NOT WANT.<BR>

THIS IS NOT A BUG FREE SOFTWARE AND MANY FUNCTIONALITIES HAVE NOT BEEN TESTED.<BR>
USE THIS SOFTWARE AT YOUR OWN RISK.<BR>

<BR>


Updates
---

- 3 July: Added support for the new ETrade APIs.

<BR>


Features
---

- can list positions, accounts, orders
- can place and cancel orders
- allows for the creation of background jobs collecting information about equities and making investment decision (some of these features are not tested)
- realtime data visualization and processing

![Alt text](commands.png?raw=true "Command List")
<img src="realtime_data.png" height="50%" width="50%">

<BR>


Get Started
---

- obtain ETrade sandbox and production keys following the instruction in https://developer.etrade.com/home  

- updates keys.txt with your personal keys

- update the browser_path in settings.txt
   - update browser_path_Windows, browser_path_Linux, or browser_path_Darwin
   - this step is necessary to perform the ETrade authorization procedure

- Run either:
   - python run.py sandbox     (to start the platform in sandbox environment)
   or
   - python run.py             (to start the platform in production environment)

<BR>


Unsupported Features
---

- margin accounts are not supported

- multiple legs orders are not supported

- any features not supported by the ETrade APIs is not supported by this platform
