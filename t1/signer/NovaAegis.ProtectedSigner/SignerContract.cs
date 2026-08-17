using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace NovaAegis.ProtectedSigner;

internal sealed record SignerRequest(
    string Protocol,
    int SchemaVersion,
    string Purpose,
    string Environment,
    string BoundaryId,
    string CallerId,
    Guid RequestId,
    string Nonce,
    DateTimeOffset IssuedAt,
    DateTimeOffset ExpiresAt,
    string PolicyVersion,
    string InvariantVersion,
    string PayloadDigest,
    string SignerIdentity,
    string KeyVersion,
    Guid AuditCorrelationId);

internal sealed record ValidationResult(bool Valid, string Code, string? EnvelopeDigest);

internal static partial class SignerContract
{
    internal const string Protocol = "nova-aegis-protected-signer";
    internal const string Purpose = "nova-aegis.evidence-anchor.v1";
    internal const string Environment = "t1-pilot-offline";
    internal const string CallerId = "nova-aegis-runtime";
    internal const string SignerIdentity = "nova-aegis-t1-anchor-signer";
    internal const string KeyVersion = "v1";
    internal const int SchemaVersion = 1;
    internal static readonly TimeSpan MaximumLifetime = TimeSpan.FromSeconds(30);
    internal static readonly TimeSpan ClockSkew = TimeSpan.FromSeconds(5);

    private static readonly string[] Fields =
    [
        "audit_correlation_id", "boundary_id", "caller_id", "environment",
        "expires_at", "invariant_version", "issued_at", "key_version", "nonce",
        "payload_digest", "policy_version", "protocol", "purpose", "request_id",
        "schema_version", "signer_identity"
    ];

    [GeneratedRegex("^sha256:[0-9a-f]{64}$", RegexOptions.CultureInvariant)]
    private static partial Regex DigestPattern();

    [GeneratedRegex("^[A-Za-z0-9_-]{22,}$", RegexOptions.CultureInvariant)]
    private static partial Regex NoncePattern();

    internal static ValidationResult Validate(ReadOnlySpan<byte> json, DateTimeOffset now)
    {
        try
        {
            using JsonDocument document = JsonDocument.Parse(json.ToArray(), new JsonDocumentOptions
            {
                AllowTrailingCommas = false,
                CommentHandling = JsonCommentHandling.Disallow,
                MaxDepth = 4
            });
            if (document.RootElement.ValueKind != JsonValueKind.Object)
                return Refuse("SCHEMA_INVALID");

            Dictionary<string, JsonElement> values = new(StringComparer.Ordinal);
            foreach (JsonProperty property in document.RootElement.EnumerateObject())
            {
                if (!values.TryAdd(property.Name, property.Value))
                    return Refuse("SCHEMA_INVALID");
            }
            if (values.Count != Fields.Length || Fields.Any(field => !values.ContainsKey(field)))
                return Refuse("SCHEMA_INVALID");

            SignerRequest request = Parse(values);
            string? refusal = ValidateValues(request, now);
            if (refusal is not null)
                return Refuse(refusal);

            byte[] canonical = Canonicalize(request);
            return new(true, "VALID", Convert.ToHexStringLower(SHA256.HashData(canonical)));
        }
        catch (Exception error) when (error is JsonException or FormatException or InvalidOperationException or OverflowException)
        {
            return Refuse("SCHEMA_INVALID");
        }
    }

    private static SignerRequest Parse(Dictionary<string, JsonElement> value) => new(
        value["protocol"].GetString() ?? "",
        value["schema_version"].GetInt32(),
        value["purpose"].GetString() ?? "",
        value["environment"].GetString() ?? "",
        value["boundary_id"].GetString() ?? "",
        value["caller_id"].GetString() ?? "",
        Guid.ParseExact(value["request_id"].GetString() ?? "", "D"),
        value["nonce"].GetString() ?? "",
        ParseTimestamp(value["issued_at"]),
        ParseTimestamp(value["expires_at"]),
        value["policy_version"].GetString() ?? "",
        value["invariant_version"].GetString() ?? "",
        value["payload_digest"].GetString() ?? "",
        value["signer_identity"].GetString() ?? "",
        value["key_version"].GetString() ?? "",
        Guid.ParseExact(value["audit_correlation_id"].GetString() ?? "", "D"));

    private static DateTimeOffset ParseTimestamp(JsonElement value)
    {
        string text = value.GetString() ?? "";
        if (!text.EndsWith('Z'))
            throw new FormatException("Signer timestamps must use UTC Z notation.");
        return DateTimeOffset.Parse(
            text,
            CultureInfo.InvariantCulture,
            DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);
    }

    private static string? ValidateValues(SignerRequest request, DateTimeOffset now)
    {
        if (request.Protocol != Protocol || request.SchemaVersion != SchemaVersion)
            return "SCHEMA_INVALID";
        if (request.Purpose != Purpose)
            return "PURPOSE_REFUSED";
        if (request.Environment != Environment || request.CallerId != CallerId)
            return "CALLER_UNAUTHORIZED";
        if (request.SignerIdentity != SignerIdentity)
            return "IDENTITY_MISMATCH";
        if (request.KeyVersion != KeyVersion)
            return "KEY_VERSION_MISMATCH";
        if (string.IsNullOrWhiteSpace(request.BoundaryId) || request.BoundaryId.Length > 128)
            return "SCHEMA_INVALID";
        if (string.IsNullOrWhiteSpace(request.PolicyVersion) || string.IsNullOrWhiteSpace(request.InvariantVersion))
            return "SCHEMA_INVALID";
        if (!DigestPattern().IsMatch(request.PayloadDigest) || !NoncePattern().IsMatch(request.Nonce))
            return "SCHEMA_INVALID";
        if (request.IssuedAt > now + ClockSkew || request.ExpiresAt <= now || request.ExpiresAt <= request.IssuedAt)
            return "REQUEST_EXPIRED";
        if (request.ExpiresAt - request.IssuedAt > MaximumLifetime)
            return "REQUEST_EXPIRED";
        return null;
    }

    internal static byte[] Canonicalize(SignerRequest request)
    {
        using MemoryStream stream = new();
        using (Utf8JsonWriter writer = new(stream, new JsonWriterOptions { Indented = false }))
        {
            writer.WriteStartObject();
            writer.WriteString("audit_correlation_id", request.AuditCorrelationId.ToString("D"));
            writer.WriteString("boundary_id", request.BoundaryId);
            writer.WriteString("caller_id", request.CallerId);
            writer.WriteString("environment", request.Environment);
            writer.WriteString("expires_at", request.ExpiresAt.ToUniversalTime().ToString("O"));
            writer.WriteString("invariant_version", request.InvariantVersion);
            writer.WriteString("issued_at", request.IssuedAt.ToUniversalTime().ToString("O"));
            writer.WriteString("key_version", request.KeyVersion);
            writer.WriteString("nonce", request.Nonce);
            writer.WriteString("payload_digest", request.PayloadDigest);
            writer.WriteString("policy_version", request.PolicyVersion);
            writer.WriteString("protocol", request.Protocol);
            writer.WriteString("purpose", request.Purpose);
            writer.WriteString("request_id", request.RequestId.ToString("D"));
            writer.WriteNumber("schema_version", request.SchemaVersion);
            writer.WriteString("signer_identity", request.SignerIdentity);
            writer.WriteEndObject();
        }
        return stream.ToArray();
    }

    private static ValidationResult Refuse(string code) => new(false, code, null);
}