# Me Tracker (SQL)

This Python-based application automates the process of tracking new orders and customers for **Mektup Evi** using Selenium. It also integrates with the NetGSM API for sending SMS notifications.

## Features

- **Order Tracking**: Automatically tracks new orders.
- **Customer Management**: Tracks customer information.
- **SMS Notifications**: Uses NetGSM API for sending updates via SMS.
- **Telegram Integration**: Sends updates through a Telegram bot.

## Setup

### Prerequisites

- Python 3.x
- Selenium
- NetGSM API credentials

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/burakpekisik/me_tracker_sql.git
   ```

2. Configure your NetGSM API keys and Telegram bot credentials by creating `userInfo.py` file.

### Running the Application

Run the application:
```bash
python main.py
```

## Folder Structure

```plaintext
├── auto_message.py      # Automation for messaging
├── main.py              # Entry point
├── send_sms.py          # SMS sending logic via NetGSM API
├── telegram_bot.py       # Telegram bot integration
```

## License

This project is licensed under the MIT License.
