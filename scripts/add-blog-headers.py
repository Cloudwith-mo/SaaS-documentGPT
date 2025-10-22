import glob
import re

header = '''<header class="fixed top-0 w-full bg-white/90 backdrop-blur-sm border-b border-gray-200 z-50">
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
<div class="flex justify-between items-center h-16">
<a href="/" class="flex items-center gap-2">
<div class="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500"></div>
<span class="text-xl font-bold">DocumentGPT</span>
</a>
<nav class="hidden md:flex items-center gap-8">
<a href="/pricing.html" class="text-sm text-gray-600 hover:text-gray-900">Pricing</a>
<a href="/teams.html" class="text-sm text-gray-600 hover:text-gray-900">Teams</a>
<a href="/about.html" class="text-sm text-gray-600 hover:text-gray-900">About</a>
<a href="/blog/index.html" class="text-sm text-gray-600 hover:text-gray-900">Blog</a>
</nav>
<a href="/app.html" class="px-4 py-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white text-sm font-semibold rounded-lg">Start free</a>
</div>
</div>
</header>'''

footer = '''<footer class="py-16 px-4 border-t border-gray-200 bg-gray-50 mt-20">
<div class="max-w-7xl mx-auto">
<div class="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
<div><h4 class="font-semibold text-gray-900 mb-4">Product</h4><ul class="space-y-3 text-sm text-gray-600"><li><a href="/features.html" class="hover:text-gray-900">Features</a></li><li><a href="/pricing.html" class="hover:text-gray-900">Pricing</a></li><li><a href="/use-cases.html" class="hover:text-gray-900">Use Cases</a></li><li><a href="/app.html" class="hover:text-gray-900">Try for Free</a></li></ul></div>
<div><h4 class="font-semibold text-gray-900 mb-4">Solutions</h4><ul class="space-y-3 text-sm text-gray-600"><li><a href="/use-cases.html#students" class="hover:text-gray-900">For Students</a></li><li><a href="/use-cases.html#researchers" class="hover:text-gray-900">For Researchers</a></li><li><a href="/use-cases.html#writers" class="hover:text-gray-900">For Writers</a></li><li><a href="/teams.html" class="hover:text-gray-900">For Teams</a></li></ul></div>
<div><h4 class="font-semibold text-gray-900 mb-4">Resources</h4><ul class="space-y-3 text-sm text-gray-600"><li><a href="/blog/index.html" class="hover:text-gray-900">Blog</a></li><li><a href="/blog/how-to-summarize-pdf.html" class="hover:text-gray-900">PDF Guide</a></li><li><a href="/blog/ai-writing-assistant-productivity.html" class="hover:text-gray-900">Writing Tips</a></li><li><a href="/blog/chat-with-documents.html" class="hover:text-gray-900">Chat Guide</a></li></ul></div>
<div><h4 class="font-semibold text-gray-900 mb-4">Company</h4><ul class="space-y-3 text-sm text-gray-600"><li><a href="/about.html" class="hover:text-gray-900">About</a></li><li><a href="mailto:support@documentgpt.io" class="hover:text-gray-900">Contact</a></li><li><a href="mailto:support@documentgpt.io" class="hover:text-gray-900">Support</a></li></ul></div>
<div><h4 class="font-semibold text-gray-900 mb-4">Legal</h4><ul class="space-y-3 text-sm text-gray-600"><li><a href="#" class="hover:text-gray-900">Privacy</a></li><li><a href="#" class="hover:text-gray-900">Terms</a></li></ul></div>
</div>
<div class="pt-8 border-t border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
<a href="/" class="flex items-center gap-2"><div class="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500"></div><span class="text-xl font-bold">DocumentGPT</span></a>
<div class="text-sm text-gray-500">© 2024 DocumentGPT. All rights reserved.</div>
</div>
</div>
</footer>'''

files = glob.glob('web/blog/*.html')
files = [f for f in files if 'index.html' not in f]

for filepath in files:
    with open(filepath, 'r') as f:
        content = f.read()
    
    if 'Inter' not in content:
        content = content.replace('<style>', '<style>@import url(\'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap\');body{font-family:\'Inter\',sans-serif}')
    
    if 'fixed top-0 w-full' not in content:
        content = re.sub(r'(<body[^>]*>)', r'\1\n' + header, content)
    
    if 'py-16 px-4 border-t border-gray-200 bg-gray-50' not in content:
        content = content.replace('</body>', footer + '\n</body>')
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Updated {filepath}")

print(f"\nTotal: {len(files)} files")
