# pkg/frontend/api/containers/lambda_clean_audio/modules/init.py

import os
import shutil
import logging
from df.enhance import init_df

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TMP_MODEL_DIR = '/tmp/deepfilter_models'

def copy_model_files():
    """Copy the model files from /opt/deepfilter_models/ to /tmp/deepfilter_models/."""
    if not os.path.exists(TMP_MODEL_DIR):
        shutil.copytree('/opt/deepfilter_models/', TMP_MODEL_DIR)
        logger.info(f"Copied model files from /opt/deepfilter_models/ to {TMP_MODEL_DIR}")
    else:
        logger.info(f"Model files already exist in {TMP_MODEL_DIR}")

    # Log the contents of the model directory to verify all necessary files are present
    logger.info("Listing the contents of the model directory:")
    for root, dirs, files in os.walk(TMP_MODEL_DIR):
        for filename in files:
            logger.info(f"Found file: {os.path.join(root, filename)}")

def load_deepfilter_model(model, df_state):
    """Load and initialize the DeepFilter model if not already loaded."""
    if model is None or df_state is None:
        logger.info("Preparing model files and loading DeepFilter...")

        # Copy the model files
        copy_model_files()

        # Load the model using the copied directory
        model, df_state, _ = init_df(model_base_dir=TMP_MODEL_DIR)

        logger.info("DeepFilter model loaded and initialized.")
    else:
        logger.info("DeepFilter model is already loaded.")
    
    return model, df_state


