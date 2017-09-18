#!/bin/sh

if [ -t 0 ]; then stty -echo -icanon -icrnl time 0 min 0; fi

count=0
keypress=''
while [ "$keypress" != "q" ]; do
  let count+=1
  echo -ne $count'\r'
  keypress="`cat -v`"
done

if [ -t 0 ]; then stty sane; fi

echo "You pressed '$keypress' after $count loop iterations"
echo "Thanks for using this script."
exit 0
