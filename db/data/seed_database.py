#!/usr/bin/env python3
"""
Script to seed the database with test data from test_data.csv
"""

import csv
import sqlite3
import subprocess
import time
from pathlib import Path


def extract_csv_if_needed():
    """Extract test_data.csv from test_data.csv.7z if needed"""
    csv_path = Path("test_data.csv")
    archive_path = Path("test_data.csv.7z")

    # If CSV already exists, no need to extract
    if csv_path.exists():
        return True

    # If archive doesn't exist, we can't extract
    if not archive_path.exists():
        print(f"Error: Neither {csv_path} nor {archive_path} found")
        return False

    # Extract the CSV file
    print(f"Extracting {archive_path}...")
    try:
        result = subprocess.run(  # noqa: S603
            ["7z", "x", str(archive_path), "-y"],  # -y for yes to all prompts  # noqa: S607
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
            check=False,
        )

        if result.returncode != 0:
            print(f"Error extracting archive: {result.stderr}")
            return False

        if not csv_path.exists():
            print("Error: CSV file not found after extraction")
            return False

        print(f"✅ Successfully extracted {csv_path}")
        return True

    except FileNotFoundError:
        print("Error: 7zip not found. Please install 7zip to use compressed data files.")
        return False
    except Exception as e:
        print(f"Error during extraction: {e}")
        return False


def seed_database():
    # Database path
    db_path = Path("../../workspace/spyplane.db")

    # Extract CSV if needed
    if not extract_csv_if_needed():
        return False

    # CSV file path (relative to this script)
    csv_path = Path("test_data.csv")

    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        return False

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Please run the database setup first")
        return False

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Clear existing data
        print("Clearing existing scout_systems data...")
        cursor.execute("DELETE FROM scout_systems")

        # Read CSV and insert data
        print(f"Reading data from {csv_path}...")
        with csv_path.open() as file:
            csv_reader = csv.reader(file)

            systems_to_insert = []
            scout_systems_to_insert = []
            current_time = int(time.time())

            for row in csv_reader:
                if len(row) >= 2:
                    system_name = row[0].strip()
                    priority_num = int(row[1].strip())

                    # Convert numeric priority to text
                    if priority_num == 1:
                        priority_text = "Primary"
                    elif priority_num == 2:
                        priority_text = "Secondary"
                    elif priority_num == 3:
                        priority_text = "Tertiary"
                    else:
                        print(f"Warning: Unknown priority {priority_num} for system {system_name}")
                        continue

                    # Add to systems table (if not already exists)
                    systems_to_insert.append((system_name,))

                    # Add to scout_systems table
                    scout_systems_to_insert.append((system_name, priority_text, "seed_script", current_time))

        # Insert systems into systems table
        print("Inserting systems into systems table...")
        cursor.executemany("INSERT OR IGNORE INTO systems (name) VALUES (?)", systems_to_insert)

        # Insert scout systems
        print("Inserting scout systems...")
        cursor.executemany(
            "INSERT INTO scout_systems (system_name, priority, added_by, added_at) VALUES (?, ?, ?, ?)",
            scout_systems_to_insert,
        )

        # Commit changes
        conn.commit()

        # Print summary
        cursor.execute("SELECT COUNT(*) FROM systems")
        systems_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM scout_systems")
        scout_count = cursor.fetchone()[0]

        cursor.execute("SELECT priority, COUNT(*) FROM scout_systems GROUP BY priority")
        priority_counts = cursor.fetchall()

        print("\n✅ Database seeded successfully!")
        print(f"📊 Systems in systems table: {systems_count}")
        print(f"📊 Tracked systems: {scout_count}")
        print("\n📈 Priority breakdown:")
        for priority, count in priority_counts:
            print(f"  {priority}: {count}")

        # Optionally clean up extracted CSV file
        if Path("test_data.csv.7z").exists() and csv_path.exists():
            print(f"\n🧹 Cleaning up extracted {csv_path}...")
            try:
                csv_path.unlink()
                print("✅ Cleanup completed")
            except Exception as e:
                print(f"⚠️  Warning: Could not remove {csv_path}: {e}")

        return True

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    print("🌱 Seeding database with test data...")
    success = seed_database()
    if success:
        print("🎉 Database seeding completed successfully!")
    else:
        print("💥 Database seeding failed!")
        exit(1)
