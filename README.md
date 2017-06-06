# MIGRO - uploadcare migration tool

Migro is a migration tool from Uploadcare team. It helps you to migrate your files 
from other cloud file management services such as Filestack, Cloudinary and etc.

Currently we support migration from Filestack but you can migrate from any service - you just need only files URLs for utility to import.
 
#### Usage

    $ > migro <PUBLIC_KEY> <INPUT_FILE>
    
 Where:
  
  `<PUBLIC_KEY>` - Your Uploadcare project public key.
  
  `<INPUT_FILE>` - Text file contains list of file URL's to upload to Uploadcare.
    
 Other options:
  
 ```
  -v, --version                   Show utility version and quit.
  
  -h, --help                      Show this help and quit.
  
  -o, --output_file PATH          Path where to place output file with
                                  results.  [default: migro_result.txt]
                                  
  --upload_base TEXT              Uploadcare upload base URL.  [default:
                                  https://upload.uploadcare.com/]
                                  
  --from_url_timeout FLOAT        Number of seconds to wait till the file will
                                  be processed by `from_url` upload.
                                  [default: 30]
                                  
  --max_uploads INTEGER           Maximum number of 'parallel' upload
                                  requests.  [default: 20]
                                  
  --max_checks INTEGER            Maximum number of 'parallel' `from_url`
                                  status check requests.  [default: 20]
                                  
  --check_interval FLOAT          Number of seconds to wait between each
                                  requests of status check for one uploaded
                                  file.
                                  
  ```              
#### How does it work

The migration process is very simple - you pass the list of files URL's(or Filestack file handles)
you want to migrate to Uploadcare to the utility and they will be uploaded to your Uploadcare project. That's it.

Utility do not download any files it's just use Uploadcare upload API - from url - https://uploadcare.com/documentation/upload/#from-url
to download files to Uploadcare site.


As the result you will get file which will contains list of uploaded files and their statuses and errors(if any).

Like this:

    https://ucarecdn.com/9e383a6b-35a5-4612-ad86-5f84c64a152b/ success https://ucarecdn.com/d8f8de4b-f92e-41a0-b7f9-28fd4baad9ae/
    https://ucarecdn.com/6a200842-df2e-4dd6-9bcd-060237c99d44/ success https://ucarecdn.com/4a03f3d4-2bd3-456e-89a5-008190980248/
    https://ucarecdn.com/03452277-724a-40ff-8ff8-3d50801fcbe8/ failed  Uploading of these files types is not allowed on your current plan. 

#### Examples

    $ > migro 9a598e2a47fe961ea412 fileslist.txt -output_file /tmp/migro-result.txt
    
And utility output will be like this:
    
    Upload progress: 100%|████████████████████████████████████████████████| 6/6 [00:03<00:00,  1.74s/file]
    All files have been process, output file with results placed here: /tmp/migro-result.txt


#### Alternatives

You can use any of our libraries we have on github for different programming languages to migrate your files from anywhere you want.

Full list of libraries you can find at https://uploadcare.com/documentation/libs/

#### Installation

   This utility require python 3.5.

   In order to install `migro`, simply run:
   
   `pip install uploadcare-migro`
    
  