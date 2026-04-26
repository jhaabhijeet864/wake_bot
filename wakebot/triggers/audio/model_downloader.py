import os
import urllib.request
import zipfile
import shutil

class ModelDownloader:
    """Handles downloading and extracting the Vosk model automatically."""
    
    @staticmethod
    def ensure_model_exists(model_path: str, url: str, logger=None):
        if os.path.exists(model_path) and os.path.isdir(model_path):
            # Check if it has required model files (e.g., am, conf, graph)
            if any(fname.endswith('.mdl') or fname == 'am' or fname == 'conf' for fname in os.listdir(model_path)):
                return True
        
        if logger:
            logger.info(f"Model not found at {model_path}. Downloading from {url}...")
            logger.info("This may take a few minutes depending on your internet connection.")
            
        zip_path = "model_temp.zip"
        
        try:
            # Download the file
            urllib.request.urlretrieve(url, zip_path)
            
            if logger:
                logger.info("Download complete. Extracting...")
                
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall("model_temp_extract")
                
            # Find the extracted model folder (it might be inside a subfolder in the zip)
            extracted_items = os.listdir("model_temp_extract")
            if len(extracted_items) == 1 and os.path.isdir(os.path.join("model_temp_extract", extracted_items[0])):
                extracted_folder = os.path.join("model_temp_extract", extracted_items[0])
            else:
                extracted_folder = "model_temp_extract"
                
            # Move the contents to the target model path
            if os.path.exists(model_path):
                shutil.rmtree(model_path)
            shutil.move(extracted_folder, model_path)
            
            if logger:
                logger.info(f"Model successfully installed to {model_path}")
                
            return True
            
        except Exception as e:
            if logger:
                logger.error(f"Failed to download or extract model: {e}")
            return False
            
        finally:
            # Cleanup temporary files
            if os.path.exists(zip_path):
                os.remove(zip_path)
            if os.path.exists("model_temp_extract"):
                shutil.rmtree("model_temp_extract", ignore_errors=True)
