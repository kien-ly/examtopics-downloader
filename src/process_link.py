import csv

# Read the .txt file

source = 'pmi'
with open(f'../results/link/{source}-link.txt', 'r') as f:
    lines = f.readlines()

# Platform to prefix mapping
platform_prefix = {
    'Amazon': 'AWS',
    'Microsoft': 'Azure',
    'google': 'GCP',
    # Add more platforms as needed
}

# Prepare data list
data = []
for line in lines:
    url = line.strip()
    if not url:
        continue
    
    # Extract platform from URL
    platform = url.split('/')[4].capitalize()  # e.g., 'amazon' -> 'Amazon'
    pre_title = platform_prefix.get(platform, platform)  # Use prefix if available, else platform name
    
    # Extract slug from URL
    slug = url.split('/')[-2]
    
    # Remove 'aws-certified-' or 'aws-' prefix if present
    if slug.startswith('aws-certified-'):
        slug_clean = slug[len('aws-certified-'):]
    elif slug.startswith('aws-'):
        slug_clean = slug[len('aws-'):]
    else:
        slug_clean = slug
    
    # Generate title: capitalize words, replace hyphens with spaces, adjust for 'Specialty'
    title_words = slug_clean.split('-')
    title = pre_title + ' ' + ' '.join(word.capitalize() for word in title_words)
    title = title.replace(' Specialty', ' - Specialty')
    
    # Extract code
    if slug_clean.endswith('-specialty'):
        # code = '-'.join(slug_clean.split('-')[-2:]).lower()
        code = '-'.join(slug_clean.split('-')[-2:])
    else:
        code_parts = slug_clean.split('-')[-2:]
        # code = '-'.join(code_parts).lower()
        code = '-'.join(code_parts)
    
    # Append to data
    data.append([platform, title, code, slug, url])

# Write to CSV
with open(f'../src/{source}_cert.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Platform', 'Certification Title', 'Certification Code', 'Certification Slug', 'Certification link'])
    writer.writerows(data)

print(f"CSV file '../src/{source}_cert.csv' created successfully.")