# Backend Integration Guide

## Service Summary

### What is the Transaction Log Viewer?

The Transaction Log Viewer is a Streamlit-based web dashboard that displays transaction logs in real-time. It reads transaction data from an AWS S3 bucket and provides an interactive interface for viewing, filtering, and analyzing transactions.

**Current Status**: Stage 1 - Local Development Complete ✅ | Production Deployment Pending ⏳
- ✅ Service is fully functional **locally** (using local file system)
- ✅ All features working: filtering, search, detailed views with three representations
- ⏳ **NOT yet deployed to production** (not pushed to GitHub, not on EC2)
- ⏳ **NOT yet connected to S3** (currently only works with local data)
- ⏳ **NOT accessible at `transaction-logs.overart.us`** (deployment pending)

**Important Order of Operations**:
1. **FIRST**: Backend must be modified to push transactions to S3 (Stage 2)
2. **THEN**: Deploy the viewer service to read from S3 (Stage 3)

**Why this order?** The viewer service reads from S3. If there's no data in S3, the viewer will show "No transaction logs found". The backend must start pushing data to S3 first, then we deploy the viewer to consume that data.

**Next Stage**: Stage 2 - Backend Integration
- Your task: Modify the backend application to push transaction text responses to S3
- Once backend is pushing to S3, we'll deploy the viewer service (Stage 3)

### Key Features

- **Real-time Dashboard**: View all transactions in a clean, searchable interface
- **Date Filtering**: Filter by Today, Yesterday, Last 7 Days, or Custom Date
- **Status Metrics**: See counts for Successful, Pending, and Failed transactions
- **Search**: Find transactions by Transaction ID
- **Detailed Views**: Three representations per transaction:
  - **Raw Text**: Original transaction text as received
  - **JSON (Full)**: All fields including null values
  - **JSON (Compact)**: Filtered view without nulls

### Architecture Overview

**Current State (Local Development)**:
```
Local Development
    ├── Backend Application (Not yet integrated)
    ├── Transaction Log Viewer (Local only)
    │   └── Reads from local_data/logs/ (file system)
    └── Accessible at http://localhost:8501
```

**Target State (Production)**:
```
Backend Application (Your Code)
    ↓
    [Pushes transaction text to S3] ← Stage 2: Your task
    ↓
S3 Bucket (transaction-logs-overart)
    ├── logs/
    │   └── YYYY/MM/DD/
    │       └── transaction_{id}.json
    ↓
Transaction Log Viewer (Streamlit App) ← Stage 3: Deploy after backend
    ├── Reads from S3
    ├── Parses and displays data
    └── Accessible at transaction-logs.overart.us
```

**Note**: The viewer currently works locally with file-based data. For production, it needs to read from S3, which requires:
1. Backend pushing data to S3 (Stage 2)
2. Viewer deployed to EC2 with IAM role for S3 access (Stage 3)

---

## S3 Data Format Requirements

### ⚡ Simplified Approach: Raw Text Files Only

**Good news!** The viewer now handles all parsing automatically. Your backend only needs to upload **raw transaction text** - no parsing, no JSON structure, no complex formatting required.

### Folder Structure

The viewer expects transactions to be stored in S3 with this **exact** structure:

```
s3://transaction-logs-overart/
└── logs/
    └── YYYY/          (4-digit year, e.g., "2025")
        └── MM/        (2-digit month, e.g., "12")
            └── DD/    (2-digit day, e.g., "16")
                └── transaction_{transaction_id}.txt
```

**Example Path**:
```
s3://transaction-logs-overart/logs/2025/12/16/transaction_2eb38251-7909-4204-9f76-4306738990b2.txt
```

### File Naming Convention

- **Format**: `transaction_{transaction_id}.txt`
- **Extension**: Must be `.txt` (not `.json`)
- **Transaction ID**: Use the actual transaction ID from your data
- **Sanitization**: Replace any non-alphanumeric characters (except `-` and `_`) with `_`
- **Example**: If transaction ID is `abc-123.xyz`, filename becomes `transaction_abc-123_xyz.txt`

### File Content

**That's it!** Just upload the raw transaction text exactly as you receive it. The viewer will:
- ✅ Parse the text automatically
- ✅ Generate all three representations (raw_text, json_full, json_compact)
- ✅ Extract transaction ID, timestamp, status, amount, etc.
- ✅ Normalize status values
- ✅ Handle all null values

### Example Transaction File

**File**: `transaction_2eb38251-7909-4204-9f76-4306738990b2.txt`

**Content** (just paste the raw text as-is):
```
Transaction[type=Optional[transaction], id=2eb38251-7909-4204-9f76-4306738990b2, reconciliationId=1Q7gL6MYhzBJkN54ZIXVSs, merchantAccountId=secure-fields-capture, currency=CAD, amount=1591, status=TransactionStatus [value=authorization_succeeded], authorizedAmount=1591, capturedAmount=0, refundedAmount=0, settledCurrency=JsonNullable[null], settledAmount=0, settled=false, country=JsonNullable[CA], externalIdentifier=JsonNullable[2eae3521-bc87-4011-9784-9570da82cd81], intent=TransactionIntent [value=authorize], paymentMethod=JsonNullable[TransactionPaymentMethod[type=Optional[payment-method], approvalUrl=JsonNullable[null], country=JsonNullable[null], currency=JsonNullable[null], details=JsonNullable[PaymentMethodDetailsCard[bin=JsonNullable[222240], cardType=JsonNullable[null], cardIssuerName=JsonNullable[null]]], expirationDate=JsonNullable[03/30], fingerprint=JsonNullable[b959707dff1ec859c26ee892e1e4677e27f287747899cdf04bb51a94f340c96a], label=JsonNullable[0005], lastReplacedAt=JsonNullable[null], method=Method [value=card], mode=JsonNullable[Mode [value=card]], scheme=JsonNullable[CardScheme [value=mastercard]], id=JsonNullable[6124914f-647b-4432-8a45-b1db2c99d6e9], approvalTarget=JsonNullable[null], externalIdentifier=JsonNullable[null], paymentAccountReference=JsonNullable[J6g5Tn5q3lYevGvDCHaxNrtscFuCz]]], method=JsonNullable[Method [value=card]], instrumentType=JsonNullable[InstrumentType [value=pan]], errorCode=JsonNullable[null], paymentService=JsonNullable[TransactionPaymentService[type=Optional[payment-service], id=1af984c1-ebd8-4304-b6a7-db6d22f5994f, paymentServiceDefinitionId=adyen-card, method=Method [value=card], displayName=Adyen]], pendingReview=Optional[false], buyer=JsonNullable[TransactionBuyer[type=Optional[buyer], id=JsonNullable[bc5ffad0-1083-41ac-8910-8426b0fb6ed0], displayName=JsonNullable[James MacDonald], externalIdentifier=JsonNullable[buyer_1765916615177], billingDetails=JsonNullable[BillingDetailsOutput[firstName=JsonNullable[James], lastName=JsonNullable[MacDonald], emailAddress=JsonNullable[james.macdonald@example.ca], phoneNumber=JsonNullable[+14035550404], address=JsonNullable[Address[city=JsonNullable[Calgary], country=JsonNullable[CA], postalCode=JsonNullable[T2S 0A1], state=JsonNullable[Alberta], stateCode=JsonNullable[CA-AB], houseNumberOrName=JsonNullable[321], line1=JsonNullable[321 17th Avenue SW], line2=JsonNullable[null], organization=JsonNullable[null]]], taxId=JsonNullable[null]]], accountNumber=JsonNullable[null]]], rawResponseCode=JsonNullable[null], rawResponseDescription=JsonNullable[null], shippingDetails=JsonNullable[ShippingDetails[firstName=JsonNullable[James], lastName=JsonNullable[MacDonald], emailAddress=JsonNullable[james.macdonald@example.ca], phoneNumber=JsonNullable[+14035550404], address=JsonNullable[Address[city=JsonNullable[Calgary], country=JsonNullable[CA], postalCode=JsonNullable[T2S 0A1], state=JsonNullable[Alberta], stateCode=JsonNullable[CA-AB], houseNumberOrName=JsonNullable[321], line1=JsonNullable[321 17th Avenue SW], line2=JsonNullable[null], organization=JsonNullable[null]]], id=JsonNullable[78ff3f88-0bcd-41b6-9fa3-7c452141c8c2], buyerId=JsonNullable[bc5ffad0-1083-41ac-8910-8426b0fb6ed0], type=Optional[shipping-details]]], checkoutSessionId=JsonNullable[null], giftCardRedemptions=[], giftCardService=JsonNullable[null], createdAt=2025-12-16T20:23:36.201957Z, updatedAt=2025-12-16T20:23:37.664110Z, disputed=false, airline=JsonNullable[null], authResponseCode=JsonNullable[null], avsResponseCode=JsonNullable[null], cvvResponseCode=JsonNullable[CVVResponseCode [value=match]], antiFraudDecision=JsonNullable[null], paymentSource=TransactionPaymentSource [value=ecommerce], merchantInitiated=false, isSubsequentPayment=false, cartItems=JsonNullable[[CartItem[name=Green Wall Art, quantity=1, unitAmount=1501, discountAmount=JsonNullable[0], taxAmount=JsonNullable[0], externalIdentifier=JsonNullable[null], sku=JsonNullable[2], productUrl=JsonNullable[https://overart.us/products/2], imageUrl=JsonNullable[null], categories=JsonNullable[null], productType=JsonNullable[null], sellerCountry=JsonNullable[null], taxExempt=JsonNullable[null], unitOfMeasure=JsonNullable[null], commodityCode=JsonNullable[null], description=JsonNullable[null], dutyAmount=JsonNullable[null], shippingAmount=JsonNullable[null]]]], statementDescriptor=JsonNullable[null], schemeTransactionId=JsonNullable[H6EGQA12X1216], threeDSecure=JsonNullable[null], paymentServiceTransactionId=JsonNullable[SCN4VM75644PRQT5], additionalIdentifiers=Optional[{payment_service_authorization_id=SCN4VM75644PRQT5, payment_service_capture_id=null, payment_service_processor_id=null}], metadata=JsonNullable[null], authorizedAt=JsonNullable[2025-12-16T20:23:37.616455Z], capturedAt=JsonNullable[null], voidedAt=JsonNullable[null], canceledAt=JsonNullable[null], approvalExpiresAt=JsonNullable[null], buyerApprovalTimedoutAt=JsonNullable[null], intentOutcome=TransactionIntentOutcome [value=succeeded], multiTender=false, accountFundingTransaction=false, recipient=JsonNullable[null], merchantAdviceCode=JsonNullable[null], installmentCount=JsonNullable[null]]
```

**That's all you need!** The viewer automatically:
- Parses this text
- Extracts transaction ID, timestamp, status, amount, currency
- Generates `json_full` (all fields with nulls)
- Generates `json_compact` (filtered without nulls)
- Normalizes status values
- Displays everything in the dashboard

### Backward Compatibility

**Note**: The viewer also supports pre-parsed `.json` files (for existing deployments), but new uploads should use `.txt` format for simplicity.

### What the Viewer Does Automatically

When you upload a `.txt` file, the viewer:
1. Reads the raw text from S3
2. Parses it using the built-in parser
3. Extracts key fields (transaction_id, timestamp, status, amount, currency)
4. Generates `json_full` (all fields including nulls)
5. Generates `json_compact` (filtered without nulls)
6. Stores `raw_text` (original text as-is)
7. Displays all three representations in the UI

**You don't need to do any of this parsing in your backend!**

---

## Backend Integration Instructions

### Step 1: AWS Setup

#### 1.1 IAM Permissions

Your backend application needs an IAM role or user with the following S3 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::transaction-logs-overart/logs/*"
    }
  ]
}
```

**Best Practice**: Use an IAM role attached to your EC2 instance or ECS task, not access keys.

#### 1.2 S3 Bucket Details

- **Bucket Name**: `transaction-logs-overart`
- **Region**: `us-east-1`
- **Path Prefix**: `logs/`

### Step 2: Add AWS SDK Dependency

#### For Java (Maven)

Add to `pom.xml`:

```xml
<dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>s3</artifactId>
    <version>2.20.0</version>
</dependency>
```

#### For Kotlin (Gradle)

Add to `build.gradle.kts`:

```kotlin
dependencies {
    implementation("software.amazon.awssdk:s3:2.20.0")
}
```

### Step 3: Create S3 Upload Service

**⚡ Simplified!** You only need to upload raw transaction text. No parsing, no JSON structure, no complex formatting.

#### Java Example

```java
package com.overart.transaction;

import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class TransactionLogService {
    
    private static final String BUCKET_NAME = "transaction-logs-overart";
    private static final String REGION = "us-east-1";
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy/MM/dd");
    
    private final S3Client s3Client;
    
    public TransactionLogService() {
        this.s3Client = S3Client.builder()
            .region(Region.of(REGION))
            .build();
    }
    
    /**
     * Uploads raw transaction text to S3
     * 
     * @param transactionId The unique transaction ID (extracted from rawText or passed separately)
     * @param rawText The original transaction text (Transaction[...] format) - exactly as received
     * @param timestamp ISO 8601 timestamp (extracted from rawText or passed separately)
     */
    public void uploadTransaction(String transactionId, String rawText, String timestamp) {
        try {
            // Parse timestamp to get date components for folder structure
            LocalDateTime dateTime = LocalDateTime.parse(
                timestamp.replace("Z", ""),
                DateTimeFormatter.ISO_DATE_TIME
            );
            String datePath = dateTime.format(DATE_FORMATTER);
            
            // Sanitize transaction ID for filename
            String safeId = sanitizeTransactionId(transactionId);
            String key = String.format("logs/%s/transaction_%s.txt", datePath, safeId);
            
            // Upload raw text to S3 (that's it!)
            PutObjectRequest putRequest = PutObjectRequest.builder()
                .bucket(BUCKET_NAME)
                .key(key)
                .contentType("text/plain")
                .build();
            
            s3Client.putObject(putRequest, RequestBody.fromString(rawText));
            
            System.out.println("Transaction uploaded: s3://" + BUCKET_NAME + "/" + key);
            
        } catch (Exception e) {
            System.err.println("Failed to upload transaction to S3: " + e.getMessage());
            e.printStackTrace();
            // Don't throw - log the error but don't break the main transaction flow
        }
    }
    
    /**
     * Sanitizes transaction ID for use in filename
     */
    private String sanitizeTransactionId(String transactionId) {
        return transactionId.replaceAll("[^a-zA-Z0-9\\-_]", "_");
    }
    
    public void close() {
        s3Client.close();
    }
}
```

#### Kotlin Example

```kotlin
package com.overart.transaction

import software.amazon.awssdk.core.sync.RequestBody
import software.amazon.awssdk.regions.Region
import software.amazon.awssdk.services.s3.S3Client
import software.amazon.awssdk.services.s3.model.PutObjectRequest
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

class TransactionLogService {
    
    companion object {
        private const val BUCKET_NAME = "transaction-logs-overart"
        private const val REGION = "us-east-1"
        private val DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy/MM/dd")
    }
    
    private val s3Client: S3Client = S3Client.builder()
        .region(Region.of(REGION))
        .build()
    
    /**
     * Uploads raw transaction text to S3
     * 
     * @param transactionId The unique transaction ID
     * @param rawText The original transaction text (Transaction[...] format) - exactly as received
     * @param timestamp ISO 8601 timestamp
     */
    fun uploadTransaction(transactionId: String, rawText: String, timestamp: String) {
        try {
            // Parse timestamp to get date components for folder structure
            val dateTime = LocalDateTime.parse(
                timestamp.replace("Z", ""),
                DateTimeFormatter.ISO_DATE_TIME
            )
            val datePath = dateTime.format(DATE_FORMATTER)
            
            // Sanitize transaction ID for filename
            val safeId = sanitizeTransactionId(transactionId)
            val key = "logs/$datePath/transaction_$safeId.txt"
            
            // Upload raw text to S3 (that's it!)
            val putRequest = PutObjectRequest.builder()
                .bucket(BUCKET_NAME)
                .key(key)
                .contentType("text/plain")
                .build()
            
            s3Client.putObject(putRequest, RequestBody.fromString(rawText))
            
            println("Transaction uploaded: s3://$BUCKET_NAME/$key")
            
        } catch (e: Exception) {
            System.err.println("Failed to upload transaction to S3: ${e.message}")
            e.printStackTrace()
            // Don't throw - log the error but don't break the main transaction flow
        }
    }
    
    /**
     * Sanitizes transaction ID for use in filename
     */
    private fun sanitizeTransactionId(transactionId: String): String {
        return transactionId.replace(Regex("[^a-zA-Z0-9\\-_]"), "_")
    }
    
    fun close() {
        s3Client.close()
    }
}
```

### Step 4: Integrate into Your Transaction Flow

**⚡ No parsing needed!** Just get the raw transaction text and upload it.

#### Example Integration Point

```java
// In your transaction processing code
public void processTransaction(Transaction transaction) {
    try {
        // ... your existing transaction processing logic ...
        
        // After transaction is processed, upload to S3
        TransactionLogService logService = new TransactionLogService();
        
        // Get the raw text representation (exactly as you receive it)
        String rawText = transaction.toString(); // Or however you get the raw Transaction[...] string
        
        // Extract transaction ID and timestamp (you may already have these)
        String transactionId = transaction.getId();
        String timestamp = transaction.getCreatedAt().toString(); // ISO 8601 format
        
        // Upload to S3 - that's it! Viewer handles all parsing
        logService.uploadTransaction(transactionId, rawText, timestamp);
        
        logService.close();
        
    } catch (Exception e) {
        // Log error but don't fail the transaction
        logger.error("Failed to log transaction to S3", e);
    }
}
```

**That's it!** No parsing, no JSON structure, no complex formatting. Just upload the raw text.

### Step 6: Error Handling

**Important**: S3 upload failures should **NOT** break your main transaction flow.

- Log errors but continue processing
- Consider retry logic for transient failures
- Use async uploads if possible to avoid blocking

```java
// Example: Async upload
CompletableFuture.runAsync(() -> {
    try {
        logService.uploadTransaction(...);
    } catch (Exception e) {
        logger.error("Async S3 upload failed", e);
    }
});
```

---

## Testing Instructions

### Step 1: Test Locally with AWS CLI

Before integrating into your backend, test the S3 upload manually:

```bash
# Create a test transaction file (just raw text!)
cat > test_transaction.txt << 'EOF'
Transaction[type=Optional[transaction], id=test-123, reconciliationId=TEST123, merchantAccountId=test-account, currency=CAD, amount=1591, status=TransactionStatus [value=authorization_succeeded], authorizedAmount=1591, createdAt=2025-12-16T20:23:36.201957Z, updatedAt=2025-12-16T20:23:37.664110Z]
EOF

# Upload to S3
aws s3 cp test_transaction.txt \
  s3://transaction-logs-overart/logs/2025/12/16/transaction_test-123.txt
```

### Step 2: Verify in Viewer

1. Go to `transaction-logs.overart.us`
2. Select "Today" or the appropriate date
3. Your test transaction should appear
4. Click on it to see the three views (Raw Text, JSON Full, JSON Compact)

### Step 3: Test from Your Backend

1. Add the S3 upload code to your backend
2. Process a test transaction
3. Check S3 to verify the file was created:
   ```bash
   aws s3 ls s3://transaction-logs-overart/logs/2025/12/16/
   ```
4. Refresh the viewer to see the new transaction

### Step 4: Verify File Structure

Check that the uploaded file exists and contains raw text:

```bash
# Download and inspect
aws s3 cp s3://transaction-logs-overart/logs/2025/12/16/transaction_test-123.txt -
```

Verify:
- ✅ File exists in correct path: `logs/YYYY/MM/DD/transaction_{id}.txt`
- ✅ File contains raw transaction text starting with `Transaction[`
- ✅ File name uses sanitized transaction ID

---

## Common Issues and Solutions

### Issue: Transaction not appearing in viewer

**Check**:
1. File path is correct: `logs/YYYY/MM/DD/transaction_{id}.txt`
2. File extension is `.txt` (not `.json`)
3. File name uses sanitized transaction ID
4. File contains valid transaction text (starts with `Transaction[`)
5. Date in path matches the transaction timestamp
6. Viewer cache (wait 5 minutes or click "Refresh")

### Issue: Parsing errors in viewer

**Solution**: 
- Ensure raw text starts with `Transaction[`
- Check that the text is complete (not truncated)
- Verify the text format matches the expected `Transaction[...]` structure

**Note**: The viewer handles status normalization and amount conversion automatically - you don't need to do this in the backend.

### Issue: S3 upload permission denied

**Solution**: 
1. Check IAM role has `s3:PutObject` permission
2. Verify bucket name is correct: `transaction-logs-overart`
3. Ensure path starts with `logs/`

### Issue: Special characters in transaction ID

**Solution**: Always sanitize the transaction ID:
```java
String safeId = transactionId.replaceAll("[^a-zA-Z0-9\\-_]", "_");
```

---

## Quick Reference

### S3 Bucket Details
- **Bucket**: `transaction-logs-overart`
- **Region**: `us-east-1`
- **Path Format**: `logs/YYYY/MM/DD/transaction_{id}.txt`
- **File Format**: Raw text (`.txt` files)

### What to Upload
- **File Content**: Raw transaction text (exactly as received)
- **File Format**: Plain text (`.txt` extension)
- **No parsing required**: Viewer handles all parsing automatically

### Testing Command
```bash
# List today's transactions
aws s3 ls s3://transaction-logs-overart/logs/$(date +%Y/%m/%d)/

# View a transaction file
aws s3 cp s3://transaction-logs-overart/logs/$(date +%Y/%m/%d)/transaction_test-123.txt -
```

---

## Support

If you encounter issues:
1. Check the [README.md](README.md) for viewer service details
2. Verify S3 permissions and bucket access
3. Test with AWS CLI first before backend integration
4. Check viewer logs: `docker logs transaction-log-viewer` on EC2

---

## Deployment Steps (Stage 3 - After Backend Integration)

**⚠️ IMPORTANT**: Complete backend integration (Stage 2) FIRST. The viewer needs data in S3 to display.

### Prerequisites Before Deployment

1. ✅ Backend is pushing transactions to S3
2. ✅ S3 bucket `transaction-logs-overart` exists and has data
3. ✅ IAM role `overart-TransactionLogReader` exists with S3 read permissions
4. ✅ GitHub repository is set up
5. ✅ Docker Hub account is ready

### Step 1: Push Code to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit: Transaction Log Viewer"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/your-org/transaction-log-viewer.git
git branch -M main
git push -u origin main
```

### Step 2: Set Up GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username | For pushing Docker images |
| `DOCKERHUB_TOKEN` | Your Docker Hub access token | Generate at hub.docker.com → Account Settings → Security |
| `EC2_ELASTIC_IP` | `52.205.10.200` | Elastic IP for EC2 instance |
| `EC2_SSH_PRIVATE_KEY` | Full private key content | SSH key for EC2 access (include `-----BEGIN` and `-----END` lines) |

### Step 3: Create S3 Bucket

```bash
# Create the S3 bucket
aws s3 mb s3://transaction-logs-overart --region us-east-1

# Verify it exists
aws s3 ls | grep transaction-logs-overart
```

### Step 4: Create IAM Role for EC2

1. Go to AWS Console → IAM → Roles → Create Role
2. Select "AWS service" → "EC2"
3. Attach policy with S3 read permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::transaction-logs-overart",
        "arn:aws:s3:::transaction-logs-overart/*"
      ]
    }
  ]
}
```

4. Name the role: `overart-TransactionLogReader`
5. Note the role ARN for EC2 setup

### Step 5: Set Up EC2 Instance

#### Option A: Using Launch Template (Recommended)

1. Follow instructions in [LAUNCH_TEMPLATE_SETUP.md](LAUNCH_TEMPLATE_SETUP.md)
2. Key settings:
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: t3.small (spot)
   - IAM role: `overart-TransactionLogReader`
   - Security group: Allow HTTP (80) and SSH (22)
   - User data: Content from `ec2-setup.sh`

3. Launch instance from template
4. Associate Elastic IP: `52.205.10.200`

#### Option B: Manual Launch

1. Launch EC2 instance:
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: t3.small (spot)
   - Security group: Create new with HTTP (80) and SSH (22) access
   - IAM role: `overart-TransactionLogReader`
   - Key pair: Create or use existing
   - User data: Copy entire content from `ec2-setup.sh`

2. Associate Elastic IP: `52.205.10.200`

3. Wait 5-7 minutes for automatic deployment

### Step 6: Verify Deployment

1. **Check EC2 instance is running**:
   ```bash
   aws ec2 describe-instances --filters "Name=ip-address,Values=52.205.10.200"
   ```

2. **SSH into instance** (if needed):
   ```bash
   ssh -i your-key.pem ubuntu@52.205.10.200
   ```

3. **Check Docker container**:
   ```bash
   docker ps | grep transaction-log-viewer
   docker logs transaction-log-viewer
   ```

4. **Check Nginx**:
   ```bash
   sudo systemctl status nginx
   ```

5. **Test the service**:
   ```bash
   curl http://localhost:8501
   # Should return HTML from Streamlit
   ```

### Step 7: Configure DNS

1. Go to your DNS provider (where `overart.us` is managed)
2. Add A record:
   - **Name**: `transaction-logs`
   - **Type**: A
   - **Value**: `52.205.10.200`
   - **TTL**: 300

3. Wait for DNS propagation (5-30 minutes)
4. Test: `nslookup transaction-logs.overart.us`

### Step 8: Verify End-to-End

1. **Backend should be pushing to S3**:
   ```bash
   aws s3 ls s3://transaction-logs-overart/logs/$(date +%Y/%m/%d)/
   # Should show transaction files
   ```

2. **Viewer should display data**:
   - Visit `http://transaction-logs.overart.us` (or `http://52.205.10.200`)
   - Should see transactions (not "No logs found")
   - Test filtering, search, and detailed views

### Step 9: Monitor and Maintain

- **Check logs**: `docker logs -f transaction-log-viewer` on EC2
- **Restart if needed**: `docker restart transaction-log-viewer`
- **Update code**: Push to GitHub → Auto-deploys via GitHub Actions

---

## Next Steps (Correct Order)

### Stage 2: Backend Integration (Do This First)

1. ⏳ Set up IAM permissions for backend (S3 write)
2. ⏳ Add AWS SDK dependency to backend
3. ⏳ Create S3 upload service in backend
4. ⏳ Integrate into transaction processing
5. ⏳ Test with sample transaction
6. ⏳ Verify data appears in S3

### Stage 3: Viewer Deployment (Do This After Backend)

1. ⏳ Push code to GitHub
2. ⏳ Set up GitHub Secrets
3. ⏳ Create S3 bucket (if not exists)
4. ⏳ Create IAM role for EC2 (S3 read)
5. ⏳ Launch EC2 instance
6. ⏳ Configure DNS
7. ⏳ Verify end-to-end

**Remember**: Backend must push data to S3 BEFORE deploying the viewer, otherwise the viewer will show "No logs found".

Good luck! 🚀

