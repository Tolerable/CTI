# Consciousness Transfer Interface (CTI)

CTI is an interactive interface for managing and interacting with multiple personas using OpenAI's GPT models.

## Features
- Create, edit, and load personas.
- Manage multiple GPT models.
- Seamlessly interact with different personas in separate tabs.

## Installation
1. Clone the repository:
    ```sh
    git clone https://github.com/Tolerable/CTI.git
    ```
2. Navigate to the project directory:
    ```sh
    cd CTI
    ```
3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage
1. Ensure your OpenAI API key is set as an environment variable:
    ```sh
    export OPENAI_API_KEY=your-api-key
    ```
2. Run the application:
    ```sh
    python CTI.py
    ```

## Note
- Make sure to configure your API key securely and avoid hardcoding it directly into your script.
- The `personas` directory and configuration files are generated automatically.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
