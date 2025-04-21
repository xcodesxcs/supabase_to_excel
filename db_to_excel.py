import os
from dotenv import load_dotenv
from supabase import create_client, Client
import csv
import sys

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
MASTER_CSV_FILE = 'participants_rows.csv'
SCHOOLS_OUTPUT_DIR = 'schools_output'
EVENTS_OUTPUT_DIR = 'events_output'

EVENTS = {
    40: "X-GAME",
    41: "X-TRIVIA",
    42: "X-PRESENT",
    43: "X-DESIGN",
    44: "X-TEMPORE",
    45: "X-BOUNTY",
    46: "X-HACK",
    47: "X-ECUTE",
    48: "X-INNOVATE",
    49: "X-PRESSION",
    50: "X-TANK",
    51: "X-CALIBRE"
}

def setup_supabase_and_schools():
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set.")
        sys.exit(1)

    try:
        supabase: Client = create_client(url, key)
        school_response = supabase.table("schools").select("id, name").execute()
        school_list_data = school_response.data
        if not school_list_data:
            print("Warning: No school data fetched from Supabase.")
            school_lookup = {}
        else:
            school_lookup = {str(school["id"]): school["name"] for school in school_list_data}
            print(f"Fetched {len(school_lookup)} schools from Supabase.")
        return school_list_data, school_lookup

    except Exception as e:
        print(f"Error connecting to Supabase or fetching schools: {e}")
        sys.exit(1)

def read_master_participants(filename=MASTER_CSV_FILE):
    all_participants = []
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            required_cols = {'name', 'phone', 'school_id', 'event_id'}
            if not required_cols.issubset(reader.fieldnames):
                missing = required_cols - set(reader.fieldnames)
                print(f"Error: Master CSV missing required columns: {missing}")
                sys.exit(1)
            all_participants = list(reader)
            if not all_participants:
                print(f"Warning: No participants found in {filename}.")
        print(f"Read {len(all_participants)} participants from {filename}.")
        return all_participants
    except FileNotFoundError:
        print(f"Error: The master file '{filename}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        sys.exit(1)

def ensure_dir_exists(dir_path):
    try:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Ensured output directory exists: {dir_path}")
    except OSError as e:
        print(f"Error creating directory {dir_path}: {e}")
        sys.exit(1)

def generate_csvs_per_school(school_list_data, all_participants, output_folder):
    print(f"\n--- Generating CSVs per School (Output: {output_folder}) ---")
    ensure_dir_exists(output_folder)

    if not school_list_data:
        print("No school data available to generate school-specific CSVs.")
        return

    processed_schools = 0
    num_schools_to_process = len(school_list_data)

    for index in range(num_schools_to_process):
        school_id = str(school_list_data[index]["id"])
        school_name = school_list_data[index]["name"]

        if school_name.lower() == "testing":
            print(f"Skipping 'Testing' school (ID: {school_id}).")
            continue

        school_file_path = os.path.join(output_folder, f'{school_name}_participants.csv')
        print(f"Processing School: {school_name} (ID: {school_id}) -> {school_file_path}")

        try:
            with open(school_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'phone', 'event']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                participants_found_for_school = False
                for event_id, event_name in EVENTS.items():
                    participants_for_this_event = []
                    for participant in all_participants:
                        part_school_id = participant.get('school_id', '').strip()
                        part_event_id = participant.get('event_id', '').strip()

                        if part_school_id == school_id and part_event_id == str(event_id):
                             participants_for_this_event.append({
                                 "name": participant.get('name', 'N/A').strip(),
                                 "phone": participant.get('phone', 'N/A').strip(),
                                 "event": event_name
                             })

                    if participants_for_this_event:
                        writer.writerows(participants_for_this_event)
                        participants_found_for_school = True

                if not participants_found_for_school:
                    print(f"  - No participants found for any event for school: {school_name}")
                else:
                    processed_schools += 1

        except IOError as e:
            print(f"Error writing file for school {school_name}: {e}")
        except Exception as e:
             print(f"An unexpected error occurred processing school {school_name}: {e}")

    print(f"\nFinished generating CSVs per school. Processed {processed_schools} non-testing schools.")

def generate_csvs_per_event(school_lookup, all_participants, output_folder):
    print(f"\n--- Generating CSVs per Event (Output: {output_folder}) ---")
    ensure_dir_exists(output_folder)

    processed_events = 0
    for event_id, event_name in EVENTS.items():
        event_participants = []
        output_filename = os.path.join(output_folder, f'{event_name}_participants.csv')
        print(f"Processing event: {event_name} (ID: {event_id}) -> {output_filename}")

        for participant in all_participants:
            participant_event_id = participant.get('event_id', '').strip()
            participant_school_id = participant.get('school_id', '').strip()

            if participant_event_id == str(event_id):
                school_name = school_lookup.get(participant_school_id, "Unknown School")

                if school_name.lower() == "testing":
                    continue

                event_participants.append({
                    "name": participant.get('name', 'N/A').strip(),
                    "phone": participant.get('phone', 'N/A').strip(),
                    "school": school_name
                })

        if event_participants:
            try:
                with open(output_filename, mode='w', newline='', encoding='utf-8') as outfile:
                    fieldnames = ['name', 'phone', 'school']
                    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(event_participants)
                print(f"  - Successfully created with {len(event_participants)} participants.")
                processed_events += 1
            except IOError as e:
                print(f"  - Error writing file: {e}")
            except Exception as e:
                print(f"  - An unexpected error occurred: {e}")
        else:
            print(f"  - No non-testing participants found for this event. CSV not created.")

    print(f"\nFinished generating CSVs per event. Created files for {processed_events} events with participants.")

if __name__ == "__main__":
    print("Starting script...")
    school_list_data, school_lookup = setup_supabase_and_schools()
    all_participants_data = read_master_participants(MASTER_CSV_FILE)
    if not all_participants_data:
         print("Exiting script as no participant data was loaded.")
         sys.exit(1)
    generate_csvs_per_school(school_list_data, all_participants_data, SCHOOLS_OUTPUT_DIR)
    generate_csvs_per_event(school_lookup, all_participants_data, EVENTS_OUTPUT_DIR)
    print("\nScript finished.")

