# PyQrzComLogbookDump
Dump logbook from qrz.com without subscription

# Usage
No qrz.com subscriber dump logbook to adif format.

Usage: python3 dump.py <xf_session> <out_adif_file>

# Example
python3 dump.py 2b00042f7481c7b056c4b410d28f33cf logbook.adif

# Get xf_session
1. login to qrz.com
2. goto logbook page
3. open browser console and read cookie ( for example console.log(document.cookie); )
4. find session value for example ...40498; xf_session=***2b00042f7481c7b056c4b410d28f33cf***; qz_userid=123...
5. copy that value and pass it to first argument
