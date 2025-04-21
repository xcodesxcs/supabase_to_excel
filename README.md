# supabase_to_excel

# STEPS TO USE THIS:
  1. Download the participants table as csv from supabase 
  2. Make a .env file and put in all the details. If you are using the env file from the nextjs codebase, remove the NEXT_PUBLIC_ from the start of the variables
  3. Currently event is hardcoded since the RLS policy is set to authenticated users only for events table, will fix this later.
  4. Run this command on the terminal to create a virtual environment:
      ```
      python3 -m venv .venv      
      ```
  5. Then run this command to activate it:
      ```
      source .venv/bin/activate
      ```
  6. Then run the script
