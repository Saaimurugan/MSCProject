#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Create DynamoDB Tables for MSC Evaluate Application
.DESCRIPTION
    This script creates the required DynamoDB tables for the MSC Evaluate application.
.PARAMETER Region
    AWS region (default: ap-south-1)
.PARAMETER Environment
    Environment name (default: dev)
#>

param(
    [string]$Region = "ap-south-1",
    [string]$Environment = "dev"
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "Creating DynamoDB Tables for MSC Evaluate" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
} catch {
    Write-Error "AWS CLI is not installed or not in PATH. Please install AWS CLI first."
    exit 1
}

# Check AWS credentials
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "AWS credentials verified" -ForegroundColor Green
} catch {
    Write-Error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
}

# Define DynamoDB tables
$tables = @(
    @{
        TableName = "msc-evaluate-users-$Environment"
        KeySchema = @(
            @{
                AttributeName = "user_id"
                KeyType = "HASH"
            }
        )
        AttributeDefinitions = @(
            @{
                AttributeName = "user_id"
                AttributeType = "S"
            },
            @{
                AttributeName = "email"
                AttributeType = "S"
            }
        )
        GlobalSecondaryIndexes = @(
            @{
                IndexName = "email-index"
                KeySchema = @(
                    @{
                        AttributeName = "email"
                        KeyType = "HASH"
                    }
                )
                Projection = @{
                    ProjectionType = "ALL"
                }
                BillingMode = "PAY_PER_REQUEST"
            }
        )
        BillingMode = "PAY_PER_REQUEST"
        Description = "User accounts and authentication data"
    },
    @{
        TableName = "msc-evaluate-templates-$Environment"
        KeySchema = @(
            @{
                AttributeName = "template_id"
                KeyType = "HASH"
            }
        )
        AttributeDefinitions = @(
            @{
                AttributeName = "template_id"
                AttributeType = "S"
            },
            @{
                AttributeName = "subject"
                AttributeType = "S"
            },
            @{
                AttributeName = "course"
                AttributeType = "S"
            },
            @{
                AttributeName = "created_by"
                AttributeType = "S"
            }
        )
        GlobalSecondaryIndexes = @(
            @{
                IndexName = "subject-course-index"
                KeySchema = @(
                    @{
                        AttributeName = "subject"
                        KeyType = "HASH"
                    },
                    @{
                        AttributeName = "course"
                        KeyType = "RANGE"
                    }
                )
                Projection = @{
                    ProjectionType = "ALL"
                }
                BillingMode = "PAY_PER_REQUEST"
            },
            @{
                IndexName = "created-by-index"
                KeySchema = @(
                    @{
                        AttributeName = "created_by"
                        KeyType = "HASH"
                    }
                )
                Projection = @{
                    ProjectionType = "ALL"
                }
                BillingMode = "PAY_PER_REQUEST"
            }
        )
        BillingMode = "PAY_PER_REQUEST"
        Description = "Quiz templates and questions"
    },
    @{
        TableName = "msc-evaluate-quiz-results-$Environment"
        KeySchema = @(
            @{
                AttributeName = "result_id"
                KeyType = "HASH"
            }
        )
        AttributeDefinitions = @(
            @{
                AttributeName = "result_id"
                AttributeType = "S"
            },
            @{
                AttributeName = "user_id"
                AttributeType = "S"
            },
            @{
                AttributeName = "template_id"
                AttributeType = "S"
            },
            @{
                AttributeName = "completed_at"
                AttributeType = "S"
            }
        )
        GlobalSecondaryIndexes = @(
            @{
                IndexName = "user-id-index"
                KeySchema = @(
                    @{
                        AttributeName = "user_id"
                        KeyType = "HASH"
                    },
                    @{
                        AttributeName = "completed_at"
                        KeyType = "RANGE"
                    }
                )
                Projection = @{
                    ProjectionType = "ALL"
                }
                BillingMode = "PAY_PER_REQUEST"
            },
            @{
                IndexName = "template-id-index"
                KeySchema = @(
                    @{
                        AttributeName = "template_id"
                        KeyType = "HASH"
                    },
                    @{
                        AttributeName = "completed_at"
                        KeyType = "RANGE"
                    }
                )
                Projection = @{
                    ProjectionType = "ALL"
                }
                BillingMode = "PAY_PER_REQUEST"
            }
        )
        BillingMode = "PAY_PER_REQUEST"
        Description = "Quiz results and student answers"
    }
)

# Function to check if table exists
function Test-DynamoDBTable {
    param([string]$TableName)
    try {
        aws dynamodb describe-table --table-name $TableName --region $Region 2>$null | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to wait for table to be active
function Wait-ForTableActive {
    param([string]$TableName)
    
    Write-Host "Waiting for table to become active: $TableName" -ForegroundColor Yellow
    
    $maxAttempts = 30
    $attempt = 0
    
    do {
        Start-Sleep -Seconds 10
        $attempt++
        
        try {
            $tableStatus = aws dynamodb describe-table --table-name $TableName --region $Region | ConvertFrom-Json
            $status = $tableStatus.Table.TableStatus
            
            if ($status -eq "ACTIVE") {
                Write-Host "Table is active: $TableName" -ForegroundColor Green
                return $true
            }
            
            Write-Host "  Status: $status (attempt $attempt/$maxAttempts)" -ForegroundColor Yellow
            
        } catch {
            Write-Host "  Checking status... (attempt $attempt/$maxAttempts)" -ForegroundColor Yellow
        }
        
    } while ($attempt -lt $maxAttempts)
    
    Write-Error "Table did not become active within expected time: $TableName"
    return $false
}

# Function to create DynamoDB table
function New-DynamoDBTable {
    param([hashtable]$TableConfig)
    
    $tableName = $TableConfig.TableName
    
    if (Test-DynamoDBTable -TableName $tableName) {
        Write-Host "Table already exists: $tableName" -ForegroundColor Green
        return $true
    }
    
    Write-Host "Creating table: $tableName" -ForegroundColor Yellow
    
    try {
        # Prepare the create table command
        $createTableJson = @{
            TableName = $tableName
            KeySchema = $TableConfig.KeySchema
            AttributeDefinitions = $TableConfig.AttributeDefinitions
            BillingMode = $TableConfig.BillingMode
        }
        
        # Add Global Secondary Indexes if they exist
        if ($TableConfig.GlobalSecondaryIndexes) {
            $createTableJson.GlobalSecondaryIndexes = $TableConfig.GlobalSecondaryIndexes
        }
        
        # Convert to JSON and save to temp file
        $jsonContent = $createTableJson | ConvertTo-Json -Depth 10
        $tempFile = "temp-table-$tableName.json"
        $jsonContent | Out-File -FilePath $tempFile -Encoding utf8
        
        # Create the table
        aws dynamodb create-table --cli-input-json file://$tempFile --region $Region | Out-Null
        
        # Clean up temp file
        Remove-Item $tempFile -ErrorAction SilentlyContinue
        
        # Wait for table to become active
        if (Wait-ForTableActive -TableName $tableName) {
            Write-Host "Table created successfully: $tableName" -ForegroundColor Green
            return $true
        } else {
            Write-Error "Failed to create table: $tableName"
            return $false
        }
        
    } catch {
        Write-Error "Failed to create table $tableName : $($_.Exception.Message)"
        return $false
    }
}

# Function to create initial admin user
function New-InitialAdminUser {
    param([string]$UsersTableName)
    
    Write-Host "Creating initial admin user..." -ForegroundColor Yellow
    
    $adminUserId = [System.Guid]::NewGuid().ToString()
    $adminEmail = "admin@msc-evaluate.com"
    $adminPassword = "Admin123!"  # Should be changed after first login
    $passwordHash = [System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($adminPassword))
    $passwordHashString = [System.BitConverter]::ToString($passwordHash).Replace("-", "").ToLower()
    
    $adminUser = @{
        user_id = @{ S = $adminUserId }
        email = @{ S = $adminEmail }
        name = @{ S = "System Administrator" }
        role = @{ S = "admin" }
        password_hash = @{ S = $passwordHashString }
        is_active = @{ BOOL = $true }
        created_at = @{ S = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ") }
        updated_at = @{ S = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ") }
    }
    
    try {
        # Check if admin user already exists
        $keyJson = @{
            user_id = @{ S = $adminUserId }
        } | ConvertTo-Json -Depth 10 -Compress
        
        $existingUser = aws dynamodb get-item --table-name $UsersTableName --key $keyJson --region $Region 2>$null
        if ($existingUser) {
            Write-Host "Admin user already exists" -ForegroundColor Blue
            return
        }
        
        # Create admin user item
        $userJson = $adminUser | ConvertTo-Json -Depth 10
        $tempFile = "temp-admin-user.json"
        $userJson | Out-File -FilePath $tempFile -Encoding utf8
        
        aws dynamodb put-item --table-name $UsersTableName --item file://$tempFile --region $Region
        
        Remove-Item $tempFile -ErrorAction SilentlyContinue
        
        Write-Host "Initial admin user created" -ForegroundColor Green
        Write-Host "   Email: $adminEmail" -ForegroundColor Cyan
        Write-Host "   Password: $adminPassword" -ForegroundColor Cyan
        Write-Host "   WARNING: Please change the password after first login!" -ForegroundColor Yellow
        
    } catch {
        Write-Warning "Failed to create initial admin user: $($_.Exception.Message)"
    }
}

# Main execution
try {
    $createdTables = @()
    
    # Create each table
    foreach ($table in $tables) {
        if (New-DynamoDBTable -TableConfig $table) {
            $createdTables += $table.TableName
        }
    }
    
    # Create initial admin user
    $usersTable = "msc-evaluate-users-$Environment"
    if ($createdTables -contains $usersTable) {
        New-InitialAdminUser -UsersTableName $usersTable
    }
    
    Write-Host "DynamoDB setup completed successfully!" -ForegroundColor Green
    Write-Host "Region: $Region" -ForegroundColor Cyan
    Write-Host "Environment: $Environment" -ForegroundColor Cyan
    Write-Host "Tables created: $($createdTables.Count)" -ForegroundColor Cyan
    
    if ($createdTables.Count -gt 0) {
        Write-Host "Created Tables:" -ForegroundColor Blue
        foreach ($tableName in $createdTables) {
            Write-Host "  - $tableName" -ForegroundColor White
        }
    }
    
} catch {
    Write-Error "DynamoDB setup failed: $($_.Exception.Message)"
    exit 1
}