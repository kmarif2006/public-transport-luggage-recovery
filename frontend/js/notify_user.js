// Notify User functionality for manager dashboard
class NotifyUserManager {
    constructor() {
        this.managerToken = localStorage.getItem('managerToken');
        this.init();
    }

    init() {
        this.attachEventListeners();
    }

    attachEventListeners() {
        // Add notify user buttons to match cards
        document.addEventListener('DOMContentLoaded', () => {
            this.addNotifyButtons();
        });
    }

    addNotifyButtons() {
        // Find all match cards and add notify buttons
        const matchCards = document.querySelectorAll('.match-card');
        
        matchCards.forEach(card => {
            if (!card.querySelector('.notify-user-btn')) {
                const notifyBtn = document.createElement('button');
                notifyBtn.className = 'notify-user-btn btn btn-success btn-sm';
                notifyBtn.innerHTML = '📧 Notify User';
                notifyBtn.onclick = () => this.notifyUser(card);
                
                const actionsDiv = card.querySelector('.match-actions') || document.createElement('div');
                actionsDiv.className = 'match-actions';
                actionsDiv.appendChild(notifyBtn);
                
                if (!card.querySelector('.match-actions')) {
                    card.appendChild(actionsDiv);
                }
            }
        });
    }

    async notifyUser(matchCard) {
        const reportId = matchCard.dataset.reportId;
        const foundId = matchCard.dataset.foundId;
        const matchScore = matchCard.dataset.matchScore;
        const userEmail = matchCard.dataset.userEmail;
        const itemName = matchCard.dataset.itemName;

        if (!confirm(`Send email notification to ${userEmail} about ${itemName}?`)) {
            return;
        }

        // Show loading
        const notifyBtn = matchCard.querySelector('.notify-user-btn');
        const originalText = notifyBtn.innerHTML;
        notifyBtn.innerHTML = '📧 Sending...';
        notifyBtn.disabled = true;

        try {
            const response = await fetch('/api/manager/notify-user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.managerToken}`
                },
                body: JSON.stringify({
                    report_id: reportId,
                    found_id: foundId,
                    match_score: matchScore
                })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Success
                notifyBtn.innerHTML = '✅ Email Sent';
                notifyBtn.className = 'notify-user-btn btn btn-success btn-sm';
                
                // Show success message
                this.showNotification(`Email sent to ${userEmail}! Verification code: ${result.verification_code}`, 'success');
                
                // Disable button after successful send
                notifyBtn.disabled = true;
                
                // Store notification record
                this.storeNotification({
                    reportId,
                    foundId,
                    userEmail,
                    itemName,
                    verificationCode: result.verification_code,
                    sentAt: new Date().toISOString()
                });
                
            } else {
                // Error
                notifyBtn.innerHTML = '❌ Failed';
                notifyBtn.className = 'notify-user-btn btn btn-danger btn-sm';
                
                this.showNotification(result.message || 'Failed to send email', 'error');
                
                // Re-enable button after error
                setTimeout(() => {
                    notifyBtn.innerHTML = originalText;
                    notifyBtn.disabled = false;
                    notifyBtn.className = 'notify-user-btn btn btn-success btn-sm';
                }, 3000);
            }
        } catch (error) {
            console.error('Error sending notification:', error);
            notifyBtn.innerHTML = '❌ Error';
            notifyBtn.className = 'notify-user-btn btn btn-danger btn-sm';
            
            this.showNotification('Network error. Please try again.', 'error');
            
            // Re-enable button after error
            setTimeout(() => {
                notifyBtn.innerHTML = originalText;
                notifyBtn.disabled = false;
                notifyBtn.className = 'notify-user-btn btn btn-success btn-sm';
            }, 3000);
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} notification-toast`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            animation: slideIn 0.3s ease-out;
        `;
        notification.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span>${message}</span>
                <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    storeNotification(notificationData) {
        // Store notification in localStorage for tracking
        const notifications = JSON.parse(localStorage.getItem('sentNotifications') || '[]');
        notifications.push({
            ...notificationData,
            id: Date.now()
        });
        localStorage.setItem('sentNotifications', JSON.stringify(notifications));
    }

    // Method to refresh notify buttons when new matches are loaded
    refreshNotifyButtons() {
        setTimeout(() => {
            this.addNotifyButtons();
        }, 100);
    }
}

// Initialize the notify user manager
const notifyUserManager = new NotifyUserManager();

// Export for use in other scripts
window.NotifyUserManager = NotifyUserManager;

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .match-actions {
        margin-top: 10px;
        text-align: right;
    }
    
    .notify-user-btn {
        margin-left: 5px;
        transition: all 0.3s ease;
    }
    
    .notify-user-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .notify-user-btn:disabled {
        opacity: 0.7;
        cursor: not-allowed;
        transform: none;
    }
`;
document.head.appendChild(style);
