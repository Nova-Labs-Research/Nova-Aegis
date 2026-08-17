using System.Text.Json;
using NovaAegis.ProtectedSigner;

if (args is ["--validate-request"])
{
    using MemoryStream input = new();
    await Console.OpenStandardInput().CopyToAsync(input);
    if (input.Length > 16 * 1024)
    {
        Console.WriteLine(JsonSerializer.Serialize(new ValidationResult(false, "SCHEMA_INVALID", null)));
        return 2;
    }
    ValidationResult result = SignerContract.Validate(input.ToArray(), DateTimeOffset.UtcNow);
    Console.WriteLine(JsonSerializer.Serialize(result));
    return result.Valid ? 0 : 2;
}

if (args is ["--candidate-manifest"])
{
    Console.WriteLine(JsonSerializer.Serialize(new
    {
        protocol = SignerContract.Protocol,
        schema_version = SignerContract.SchemaVersion,
        purpose = SignerContract.Purpose,
        environment = SignerContract.Environment,
        signer_identity = SignerContract.SignerIdentity,
        key_version = SignerContract.KeyVersion,
        provider = CngSigningBoundary.ProviderName,
        key_name = CngSigningBoundary.KeyName,
        activation = "BLOCKED_G1_CANDIDATE"
    }));
    return 0;
}

Console.Error.WriteLine("BLOCK_IMPLEMENTATION: uninstalled G1 candidate has no activation mode.");
return 3;