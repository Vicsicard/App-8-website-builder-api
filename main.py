from utils.error_logger import handle_app_error

def main():
    try:
        # Your main app logic here
        pass
        
    except Exception as e:
        handle_app_error(
            error=e,
            app_name="App8_Website_Builder",
            log_to_workflow=True
        )
        raise  # Re-raise the error after logging

if __name__ == "__main__":
    main()
