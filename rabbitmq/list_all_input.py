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


# main
directory = "/beegfs/data/input/"
mp4_data = list_mp4_files(directory)

if mp4_data:
  print(mp4_data)
else:
  print("No mp4 files found in the specified directory.")