import os

def list_mp4_files(directory):
  """
  This function lists all mp4 files within a directory.
  """

  mp4_files = []

  for filename in os.listdir(directory):
    if filename.endswith(".mp4"):
      filepath = os.path.join(directory, filename)
      mp4_files.append(filepath)
  
  return mp4_files

# Example usage
directory = "/beegfs/data/input/"  # Replace with your actual directory path
mp4_data = list_mp4_files(directory)

if not mp4_data.empty:
  print(mp4_data)
else:
  print("No mp4 files found in the specified directory.")