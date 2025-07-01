# Yoblox

Yoblox is a multiplayer game platform developed using Ursina and UrsinaNetworking.

## Contents
- [Installation](#installation)
- [Logic](#logic)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Installation
1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   python3 server.py .ybxl
   ```
3. Run the client:
   ```bash
   python3 client.py port username
   ```

## Logic
- The server file (`server.py`) runs the game's server-side. You must start it first to allow connections.
- The client file (`client.py`) allows players to connect to the game. Run this on a player's machine.
- To join a game, players need to input the server's IP address when prompted.
- Once connected, players can interact with the game world and other players in real time.
- If the server stops running, all players will be disconnected.

## Development
Developers who want to contribute can follow these steps:
1. Fork this repository.
2. Create a new branch:
   ```bash
   git checkout -b new-feature
   ```
3. Make your changes and commit them:
   ```bash
   git commit -m "Added new feature"
   ```
4. Push your changes to GitHub:
   ```bash
   git push origin new-feature
   ```
5. Create a Pull Request.

## Contributing
If you would like to contribute, please open an issue or check existing issues.

## License
This project is licensed under the [MIT License](LICENSE).

