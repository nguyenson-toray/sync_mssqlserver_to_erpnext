#!/usr/bin/env python3
"""
Cron Job Manager for Database Sync
Manages cron jobs for scheduled database synchronization
"""

import os
import subprocess
import tempfile
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CronManager:
    """Manages cron jobs for database synchronization"""
    
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.venv_python = os.path.join(self.script_dir, 'venv', 'bin', 'python')
        self.sync_script = os.path.join(self.script_dir, 'db_sync.py')
        
        # Verify paths exist
        if not os.path.exists(self.venv_python):
            raise FileNotFoundError(f"Virtual environment not found: {self.venv_python}")
        if not os.path.exists(self.sync_script):
            raise FileNotFoundError(f"Sync script not found: {self.sync_script}")
    
    def get_current_crontab(self) -> str:
        """Get current crontab content"""
        try:
            result = subprocess.run(['crontab', '-l'], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return result.stdout
            elif result.returncode == 1 and "no crontab" in result.stderr.lower():
                return ""
            else:
                raise RuntimeError(f"Failed to get crontab: {result.stderr}")
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Error accessing crontab: {e}")
    
    def set_crontab(self, content: str) -> None:
        """Set crontab content"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cron') as f:
                f.write(content)
                temp_file = f.name
            
            result = subprocess.run(['crontab', temp_file], 
                                  capture_output=True, text=True, check=True)
            os.unlink(temp_file)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to set crontab: {result.stderr}")
                
        except subprocess.SubprocessError as e:
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file)
                except:
                    pass
            raise RuntimeError(f"Error setting crontab: {e}")
    
    def remove_sync_cron_jobs(self) -> None:
        """Remove existing database sync cron jobs"""
        current_crontab = self.get_current_crontab()
        
        # Filter out lines containing our sync script
        lines = current_crontab.strip().split('\n') if current_crontab.strip() else []
        filtered_lines = []
        
        for line in lines:
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                filtered_lines.append(line)
                continue
            
            # Remove lines containing our sync script path
            if self.sync_script not in line and 'db_sync.py' not in line:
                filtered_lines.append(line)
            else:
                logger.info(f"Removing cron job: {line.strip()}")
        
        new_crontab = '\n'.join(filtered_lines)
        if new_crontab and not new_crontab.endswith('\n'):
            new_crontab += '\n'
        
        self.set_crontab(new_crontab)
        logger.info("Removed existing database sync cron jobs")
    
    def add_sync_cron_jobs(self, times: List[str]) -> None:
        """Add cron jobs for database sync at specified times"""
        current_crontab = self.get_current_crontab()
        
        # Create cron job entries
        cron_entries = []
        cron_entries.append("# Database sync cron jobs")
        
        for time_str in times:
            hour, minute = time_str.split(':')
            cron_line = f"{minute} {hour} * * * {self.venv_python} {self.sync_script} >> /var/log/db_sync.log 2>&1"
            cron_entries.append(cron_line)
            logger.info(f"Adding cron job for {time_str}: {cron_line}")
        
        # Add empty line at the end
        cron_entries.append("")
        
        # Combine with existing crontab
        new_crontab = current_crontab
        if new_crontab and not new_crontab.endswith('\n'):
            new_crontab += '\n'
        
        new_crontab += '\n'.join(cron_entries)
        
        self.set_crontab(new_crontab)
        logger.info(f"Added {len(times)} database sync cron jobs")
    
    def setup_sync_cron_jobs(self, times: List[str] = None) -> None:
        """Setup cron jobs for database sync (remove old, add new)"""
        if times is None:
            times = ['10:00', '13:00', '18:00', '23:00']
        
        logger.info("Setting up database sync cron jobs...")
        
        # Remove existing sync cron jobs
        self.remove_sync_cron_jobs()
        
        # Add new cron jobs
        self.add_sync_cron_jobs(times)
        
        logger.info("Database sync cron jobs setup completed")
    
    def list_sync_cron_jobs(self) -> List[str]:
        """List current database sync cron jobs"""
        current_crontab = self.get_current_crontab()
        sync_jobs = []
        
        lines = current_crontab.strip().split('\n') if current_crontab.strip() else []
        
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                if self.sync_script in line or 'db_sync.py' in line:
                    sync_jobs.append(line.strip())
        
        return sync_jobs
    
    def remove_all_sync_cron_jobs(self) -> None:
        """Remove all database sync cron jobs"""
        logger.info("Removing all database sync cron jobs...")
        self.remove_sync_cron_jobs()
        logger.info("All database sync cron jobs removed")

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage database sync cron jobs')
    parser.add_argument('action', choices=['setup', 'remove', 'list'], 
                       help='Action to perform')
    parser.add_argument('--times', nargs='+', default=['10:00', '13:00', '18:00', '23:00'],
                       help='Times for cron jobs (HH:MM format)')
    
    args = parser.parse_args()
    
    try:
        manager = CronManager()
        
        if args.action == 'setup':
            manager.setup_sync_cron_jobs(args.times)
            print(f"Setup cron jobs for times: {', '.join(args.times)}")
            
        elif args.action == 'remove':
            manager.remove_all_sync_cron_jobs()
            print("Removed all database sync cron jobs")
            
        elif args.action == 'list':
            jobs = manager.list_sync_cron_jobs()
            if jobs:
                print("Current database sync cron jobs:")
                for job in jobs:
                    print(f"  {job}")
            else:
                print("No database sync cron jobs found")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())