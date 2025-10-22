# Stripe Pricing Update - 2 Options Only

## Update the upgradeModal in backup.html

Replace the entire `<div id="upgradeModal">` section with:

```html
<div id="upgradeModal" class="fixed inset-0 bg-black/30 backdrop-blur-sm hidden items-center justify-center" style="z-index: 100;">
    <div class="bg-white rounded-2xl shadow-2xl w-[600px] p-6">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-bold">Choose Your Plan</h2>
            <button id="closeUpgrade" class="text-2xl opacity-50 hover:opacity-100">×</button>
        </div>
        <div class="grid grid-cols-2 gap-4">
            <!-- Monthly Plan -->
            <div class="border-2 border-gray-300 rounded-xl p-6 hover:border-emerald-500 transition">
                <div class="text-xs uppercase text-gray-600 font-semibold mb-2">Monthly</div>
                <div class="text-4xl font-bold mb-1">$9.99<span class="text-sm text-gray-500">/mo</span></div>
                <div class="text-xs text-gray-500 mb-4">Billed monthly</div>
                <div class="space-y-2 text-sm mb-6">
                    <div>✓ Unlimited chats</div>
                    <div>✓ Unlimited documents</div>
                    <div>✓ All 6 AI agents</div>
                    <div>✓ Priority support</div>
                </div>
                <button class="selectPlan w-full text-sm px-4 py-3 rounded-lg bg-gradient-to-r from-emerald-500 to-cyan-500 text-white hover:opacity-90 font-semibold" data-plan="monthly">Get Started</button>
            </div>
            
            <!-- Annual Plan -->
            <div class="border-2 border-emerald-500 rounded-xl p-6 relative bg-gradient-to-br from-emerald-50 to-cyan-50">
                <div class="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white text-xs px-3 py-1 rounded-full font-bold">60% OFF</div>
                <div class="text-xs uppercase text-emerald-600 font-semibold mb-2">Annual</div>
                <div class="text-4xl font-bold mb-1 text-emerald-600">$3.99<span class="text-sm text-gray-500">/mo</span></div>
                <div class="text-xs text-gray-500 mb-4">$47.88 billed yearly</div>
                <div class="space-y-2 text-sm mb-6">
                    <div>✓ Unlimited chats</div>
                    <div>✓ Unlimited documents</div>
                    <div>✓ All 6 AI agents</div>
                    <div>✓ Priority support</div>
                    <div class="text-emerald-600 font-semibold">✓ Save $71.88/year</div>
                </div>
                <button class="selectPlan w-full text-sm px-4 py-3 rounded-lg bg-gradient-to-r from-emerald-500 to-cyan-500 text-white hover:opacity-90 font-semibold shadow-lg" data-plan="annual">Get Started</button>
            </div>
        </div>
        <div class="text-center text-xs text-gray-500 mt-4">Cancel anytime • Secure payment via Stripe</div>
    </div>
</div>
```

## Update the selectPlan function in backup.html

Find the `selectPlan` function and replace with:

```javascript
async function selectPlan(plan) {
    if (!state.user || state.user.isGuest) {
        hideModal('upgradeModal');
        showModal('loginModal');
        toast('Please login first');
        return;
    }
    
    toast('Creating checkout session...');
    
    try {
        const res = await fetch(`${API}/subscription`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                action: 'create',
                user_id: state.user.sub,
                plan: plan
            })
        });
        
        const data = await res.json();
        
        if (res.ok && data.checkout_url) {
            // Redirect to Stripe Checkout
            window.location.href = data.checkout_url;
        } else {
            toast('Checkout failed: ' + (data.error || 'Unknown error'));
        }
    } catch (e) {
        toast('Error: ' + e.message);
    }
    
    posthog && posthog.capture('upgrade_clicked', {plan: plan});
}
```

## Pricing Breakdown

**Monthly**: $9.99/month
- Total per year: $119.88

**Annual**: $47.88/year ($3.99/month)
- Savings: $71.88/year (60% off)
- Monthly equivalent: $3.99

## Next Steps

1. Create Stripe products:
   - Monthly: $9.99/month recurring
   - Annual: $47.88/year recurring

2. Update Lambda environment variables:
   - `STRIPE_MONTHLY_PRICE_ID`: your_monthly_price_id
   - `STRIPE_ANNUAL_PRICE_ID`: your_annual_price_id

3. Test with Stripe test mode first

4. Deploy updated code
